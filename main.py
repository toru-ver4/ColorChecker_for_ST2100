#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ITU-R. BT.2100 用の ColorChecker を作る。
"""

import os
import colour
import numpy as np
import cv2


""" Target Brightness [cd/m2] を選択 """
TARGET_BRIGHTNESS = 100  # ColorChecker のピーク輝度をどこに合わせるか


""" ColorChecker を選択 """
# COLOR_CHECKER_NAME = 'ColorChecker 1976'
COLOR_CHECKER_NAME = 'ColorChecker 2005'
# COLOR_CHECKER_NAME = 'BabelColor Average'


""" Chromatic Adaptation を選択 """
# CHROMATIC_ADAPTATION_TRANSFORM = 'Bradford'
CHROMATIC_ADAPTATION_TRANSFORM = 'CAT02'


""" Color Space を選択(Gamut, WhitePoint, XYZ_to_RGB_mtx で使用) """
COLOR_SPACE = colour.models.BT2020_COLOURSPACE
# COLOR_SPACE = colour.models.BT709_COLOURSPACE
# COLOR_SPACE = colour.models.ACES_PROXY_COLOURSPACE
# COLOR_SPACE = colour.models.S_GAMUT3_COLOURSPACE
# COLOR_SPACE = colour.models.S_GAMUT3_CINE_COLOURSPACE
# COLOR_SPACE = colour.models.V_GAMUT_COLOURSPACE


""" WhitePoint を選択 """
# WHITE_POINT_STR = 'D50'
# WHITE_POINT_STR = 'D55'
# WHITE_POINT_STR = 'D60'
# WHITE_POINT_STR = 'DCI-P3'
WHITE_POINT_STR = 'D65'

WHITE_POINT = colour.colorimetry.ILLUMINANTS['cie_2_1931'][WHITE_POINT_STR]

"""
OETF を選択

HDR の OETF は一番ミスりやすい箇所。
測定目的の場合は OOTF を考慮する必要がある。

HLG の場合、モニター側で EOTF と一緒に OOTF が掛かるため
OETF では OOTF の inverse も一緒に掛ける必要がある。

一方で ST2084 の場合はモニター側で OOTF は掛からないので
素直に OETF だけ適用すれば良い。


補足だが、以下の2つの関数は内部動作が異なる(OOTFの有無)。

* OETF = colour.models.oetf_ST2084
* OETF = colour.models.oetf_BT2100_PQ
"""
# OETF_TYPE = 'HLG'
# OETF_TYPE = 'ST2084'
# OETF_TYPE = "sRGB"
OETF_TYPE = "BT1886_Reverse"  # gamma = 1/2.4


""" Image Spec """
IMG_WIDTH = 1920
IMG_HEIGHT = 1080
COLOR_CHECKER_SIZE = 1 / 4.5  # [0:1] で記述
COLOR_CHECKER_PADDING = 0.01
COLOR_CHECKER_H_NUM = 6
COLOR_CHECKER_V_NUM = 4
IMG_MAX_LEVEL = 0xFFFF


""" ColorChecker Name """
COLOR_CHECKER_EACH_NAME = [
    "dark skin", "light skin", "blue sky", "foliage",
    "blue flower", "bluish green", "orange", "purplish blue",
    "moderate red", "purple", "yellow green", "orange yellow",
    "blue", "green", "red", "yellow",
    "magenta", "cyan", "white 9.5", "neutral 8",
    "neutral 6.5", "neutral 5", "neutral 3.5", "black 2"
]


def get_colorchecker_large_xyz_and_whitepoint(cc_name=COLOR_CHECKER_NAME):
    """
    ColorChecker の XYZ値を取得する

    Parameters
    ------------
    cc_name : strings
        color space name.

    Returns
    ------------
    array_like
        ColorChecker の XYZ値
    """
    colour_checker_param = colour.COLOURCHECKERS.get(cc_name)

    # 今回の処理では必要ないデータもあるので xyY だけ抽出
    # ------------------------------------------------
    _name, data, whitepoint = colour_checker_param
    temp_xyY = []
    for _index, label, xyY in data:
        temp_xyY.append(xyY)
    temp_xyY = np.array(temp_xyY)
    large_xyz = colour.models.xyY_to_XYZ(temp_xyY)

    return large_xyz, whitepoint


def get_linear_rgb_from_large_xyz(large_xyz, whitepoint,
                                  color_space=COLOR_SPACE):
    """
    XYZ値 から RGB値（Linear）を求める

    Parameters
    ------------
    large_xyz : array_like
        colorchecker の XYZ値
    whitepoint : array_like
        colorckecker の XYZ値の whitepoint
    color_space : RGB_Colourspace
        XYZ to RGB 変換の対象となる color space

    Returns
    ------------
    array_like
        [0:1] の Linear な RGBデータ
    """
    illuminant_XYZ = whitepoint   # ColorCheckerのオリジナルデータの白色点
    illuminant_RGB = WHITE_POINT  # RGBの白色点を設定
    chromatic_adaptation_transform = CHROMATIC_ADAPTATION_TRANSFORM
    large_xyz_to_rgb_matrix = color_space.XYZ_to_RGB_matrix
    rgb = colour.models.XYZ_to_RGB(large_xyz, illuminant_XYZ, illuminant_RGB,
                                   large_xyz_to_rgb_matrix,
                                   chromatic_adaptation_transform)

    return rgb


def get_rgb_with_prime(rgb):
    """
    Linear な RGB値に ガンマカーブを掛ける

    Parameters
    ------------
    rgb : array_like
        [0:1] の Linear Data

    Returns
    ------------
    array_like
        [0:1] の Gammaが掛かったデータ
    """

    if OETF_TYPE == 'HLG':
        oetf_func = colour.models.eotf_reverse_BT2100_HLG
    elif OETF_TYPE == 'ST2084':
        oetf_func = colour.models.oetf_ST2084
    elif OETF_TYPE == 'sRGB':
        oetf_func = colour.models.oetf_sRGB
    else:
        oetf_func = None

    # [0:1] の RGB値を所望の輝度値[cd/m2] に変換。ただしHDRの場合のみ
    # ----------------------------------------
    if OETF_TYPE == 'HLG' or OETF_TYPE == 'ST2084':
        rgb_bright = rgb * TARGET_BRIGHTNESS
    else:
        rgb_bright = rgb

    # OETF 適用
    # -----------------------------------------
    if OETF_TYPE == 'BT1886_Reverse':
        rgb_prime = rgb_bright ** (1/2.4)
    else:
        rgb_prime = oetf_func(rgb_bright)

    return rgb_prime


def preview_image(img, order='rgb', over_disp=False):
    """ OpenCV の機能を使って画像をプレビューする """
    if order == 'rgb':
        cv2.imshow('preview', img[:, :, ::-1])
    elif order == 'bgr':
        cv2.imshow('preview', img)
    else:
        raise ValueError("order parameter is invalid")

    if over_disp:
        cv2.resizeWindow('preview', )
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def save_color_checker_image(rgb):
    """
    以下の2種類の画像を生成＆保存＆Previewする。

    * 24枚の測定用 ColorChecker画像。画面中央にRGBパターン表示
    * 1枚の確認用画像。1枚の画面に24枚種類の ColorChecker を表示

    Parameters
    ------------
    rgb : array_like
        [0:1] の Linear Data

    """

    # 基本パラメータ算出
    # --------------------------------------
    h_num = 6
    v_num = 4
    img_height = IMG_HEIGHT
    img_width = IMG_WIDTH
    patch_st_h = int(IMG_WIDTH / 2.0
                     - (IMG_HEIGHT * COLOR_CHECKER_SIZE
                        * COLOR_CHECKER_H_NUM / 2.0
                        + (IMG_HEIGHT * COLOR_CHECKER_PADDING
                           * (COLOR_CHECKER_H_NUM / 2.0 - 0.5)) / 2.0))
    patch_st_v = int(IMG_HEIGHT / 2.0
                     - (IMG_HEIGHT * COLOR_CHECKER_SIZE
                        * COLOR_CHECKER_V_NUM / 2.0
                        + (IMG_HEIGHT * COLOR_CHECKER_PADDING
                           * (COLOR_CHECKER_V_NUM / 2.0 - 0.5)) / 2.0))
    patch_width = int(img_height * COLOR_CHECKER_SIZE)
    patch_height = patch_width
    patch_space = int(img_height * COLOR_CHECKER_PADDING)
    measure_file_str = "./output/ColorChecker_Measure_Patch_{:s}_{:s}_{:s}_{:02d}_{:s}.tiff"
    all_patch_file_str = "./output/ColorChecker_All_{:s}_{:s}_{:s}_.tiff"

    # 24ループで1枚の画像に24パッチを描画
    # -------------------------------------------------
    img_all_patch = np.zeros((img_height, img_width, 3))
    for idx in range(h_num * v_num):
        v_idx = idx // h_num
        h_idx = (idx % h_num)
        patch = np.ones((patch_height, patch_width, 3))
        patch[:, :] = rgb[idx]
        st_h = patch_st_h + (patch_width + patch_space) * h_idx
        st_v = patch_st_v + (patch_height + patch_space) * v_idx
        img_all_patch[st_v:st_v+patch_height, st_h:st_h+patch_width] = patch

    # パッチのプレビューと保存
    # --------------------------------------------------
    preview_image(img_all_patch)
    file_name = all_patch_file_str.format(COLOR_SPACE._name,
                                          WHITE_POINT_STR, OETF_TYPE)
    cv2.imwrite(file_name, _get_16bit_img(img_all_patch[:, :, ::-1]))

    # 測定用の画面中央パッチを24種類、個別に作成
    # --------------------------------------------------
    img_each_patch = np.zeros((img_height, img_width, 3))
    patch_width = int(img_width * 0.15)
    patch_height = patch_width
    st_h = (img_width // 2) - (patch_width // 2)
    st_v = (img_height // 2) - (patch_height // 2)
    patch = np.ones((patch_height, patch_width, 3))

    for idx in range(h_num * v_num):
        patch[:, :] = rgb[idx]
        img_each_patch[st_v:st_v+patch_height, st_h:st_h+patch_width] = patch
        file_name = measure_file_str.format(COLOR_SPACE._name, WHITE_POINT_STR,
                                            OETF_TYPE, idx + 1,
                                            COLOR_CHECKER_EACH_NAME[idx])
        cv2.imwrite(file_name, _get_16bit_img(img_each_patch[:, :, ::-1]))


def _get_16bit_img(img):
    """
    16bit整数型に変換した画像データを得る

    Parameters
    ------------
    img : array_like
        [0:1] の浮動小数点の値

    Returns
    ------------
    array_like
        [0:65535] に正規化された 16bit整数型の値
    """
    return np.uint16(np.round(img * IMG_MAX_LEVEL))


def _get_10bit_img(img):
    """
    10bit整数型に変換した画像データを得る

    Parameters
    ------------
    img : array_like
        [0:1] の浮動小数点の値

    Returns
    ------------
    array_like
        [0:1023] に正規化された 10bit整数型の値
    """
    return np.uint16(np.round(img * 0x3FF))


def save_color_checker_value(large_xyz, rgb_prime):
    """
    ColorChecker の xyY値 および RGB値 を CSV ファイルに吐き出す

    Parameters
    ------------
    large_xyz : array_like
        ColorPatch の XYZ値
    rgb_prime : array_like
        ColorPatch の RGB値。ガンマカーブ適用済み。値域は[0:1]。

    """

    csv_file_str = "./output/ColorChecker_Value_{:s}_{:s}_{:s}.csv"
    csv_file = csv_file_str.format(COLOR_SPACE._name, WHITE_POINT_STR,
                                   OETF_TYPE)

    data_fmt = "{:02d}, {:s}, {:f}, {:f}, {:f}, {:d}, {:d}, {:d}\n"

    # 出力用に変換
    # ---------------------------------------------------
    """ colour.XYZ_to_xyY() は第2引数を省略するとD50になるので注意 """
    xyY_list = colour.XYZ_to_xyY(large_xyz, WHITE_POINT)
    rgb_10bit = _get_10bit_img(rgb_prime)

    with open(csv_file, 'w') as f:
        f.write("idx, name, x, y, Y, R, G, B\n")
        idx = 0
        for xyY, rgb in zip(xyY_list, rgb_10bit):
            f.write(data_fmt.format(idx + 1, COLOR_CHECKER_EACH_NAME[idx],
                                    xyY[0], xyY[1], xyY[2],
                                    rgb[0], rgb[1], rgb[2]))
            idx += 1


def main_func():
    # 所望の設定に適したRGB値を算出
    # ---------------------------------
    large_xyz, whitepoint = get_colorchecker_large_xyz_and_whitepoint()
    rgb = get_linear_rgb_from_large_xyz(large_xyz, whitepoint)
    rgb_prime = get_rgb_with_prime(rgb)

    # ColorChecker画像生成
    # ---------------------------------
    save_color_checker_image(rgb_prime)

    # xyY値、RGB値をまとめた CSVファイルを吐き出し
    # -----------------------------------------
    save_color_checker_value(large_xyz, rgb_prime)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main_func()
