# ITU-R BT.2100 向け ColorChecker 作成

## 概要

SDR の ColorChecker は RGB値が様々な場所で公開されているが、
HDR の ColorChecker は RGB値が調べる限りどこにも公開されていない。なので作る。

余談だが、本ドキュメントでは*マクベスチャート*という呼び方はせず、*ColorChecker* と呼ぶ。理由は [Wikipedia](https://en.wikipedia.org/wiki/ColorChecker) での本件の項目名が ColorChecker だったからである。

| ST.2084 | HLG(system_gamma=1.2) |
|:--------:|:-------------------:|
|![ST.2084](https://1drv.ms/u/s!Aoyl6po8qsyGt22R91aMQTwZHK-Q) | ![HLG](https://1drv.ms/u/s!Aoyl6po8qsyGt25F9KwirJOuvLk_)|

## ColorChecker の色座標データ

BabelColor が公開している [ColorChecker RGB and spectra](http://www.babelcolor.com/download/ColorChecker_RGB_and_spectra.xls) を使用する。

このファイルでは以下の3種類の ColorChecker のデータが公開されている。

* BabelColor Avg
* ColorChecker 2005
* ColorChecker 1976

今回は *ColorChecker 2005* を用いる。理由は何となくである。別のを使いたければ後述のソースコードを1行修正すれば良い。

## ColorChecker の色温度変換

公開されている ColorChecker の xyY値 は D50光源の値である。一般的なディスプレイは D65 で表示するため D50 → D65 の変換が必要となる。

色温度変換の際には *chromatic adaptation* と呼ばれる補正？をするのが一般的である。変換方式として広く使われているのは *Bradford* 方式であるが、今回は *CAT02* 方式を使用する。

理由は２つ。

* CAT02方式は ACES での色温度変換で使用可能である(Bradford か CAT02 か選択可能)
* 某社のカメラの IDT を調べたところ、CAT02方式で変換Matrixが計算されていた

もちろん、Bradford変換をしたい場合は、後述のソースコードを1行修正すれば実現できる。

## 実装とカスタマイズ

### ソースコード

```main.py``` 参照。

### 注意事項

設定する色域が狭い場合、ColorChecker の値を RGB値で正しく表現出来ない場合がある。</br>
例：BT.709色域の Cyan は Red の値が **0** に張り付き正しく表現できない

測定値が理論値と一致しない場合は ```ColorChecker_Value_GAMUT_WHITE-POINT_OETF.csv``` を開き、RGB値が **0** または **1023** に張り付いていないか確認すること。

### カスタマイズ

以下の変数を変更することにより、カスタマイズが可能である。なお、これらの変数はソースコード冒頭にまとまっている。

#### COLOR_CHECKER_NAME

3種類ある ColorChecker の中から好みのものを選べる。

```python

""" ColorChecker を選択 """
# COLOR_CHECKER_NAME = 'ColorChecker 1976'
COLOR_CHECKER_NAME = 'ColorChecker 2005'
# COLOR_CHECKER_NAME = 'BabelColor Average'

```

#### CHROMATIC_ADAPTATION_TRANSFORM

2種類ある chromatic adaptation の方式から好みのものを選べる。

```python

""" Chromatic Adaptation を選択 """
# CHROMATIC_ADAPTATION_TRANSFORM = 'Bradford'
CHROMATIC_ADAPTATION_TRANSFORM = 'CAT02'

```

#### White Point

ColorChecker の xyY値は D50光源での値である。xyY値を RGB値に変換する際、任意の白色点へマッピングすることができる。

```python

""" WhitePoint を選択 """
# WHITE_POINT_STR = 'D50'
# WHITE_POINT_STR = 'D55'
# WHITE_POINT_STR = 'D60'
# WHITE_POINT_STR = 'DCI-P3'
WHITE_POINT_STR = 'D65'

```

#### OETF

xyY値から変換したRGB値に対してかける OETF を選択する。

```python

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
OETF_TYPE = 'ST2084'
# OETF_TYPE = "sRGB"
# OETF_TYPE = "BT1886_Reverse"  # gamma = 1/2.4

```

#### Image Spec

画像サイズや ColorChecker のサイズなどを指定できる。

```python

IMG_WIDTH = 1920
IMG_HEIGHT = 1080
COLOR_CHECKER_SIZE = 1 / 4.5  # [0:1] で記述
COLOR_CHECKER_PADDING = 0.01

```

## 動作環境構築

Python で *Colour (colour science for python)* と *OpenCV* が動作すれば良い。

Windows環境であれば以下の手順が楽だと考える。

1. Anaconda のインストール
2. conda で colour をインストール
3. conda or *Unoofficial Windows Binaries for Python* を利用して OpenCV をインストール

Colour のインストールについての詳細は [Installation Guide](http://colour-science.org/installation-guide/) 参照。

OpenCV は Python のバージョンに依って手順が異なるためここには記載しない。

## 実行方法

```bash

> python main.py

```

## 生成物

./output フォルダ以下に生成される。

```python

./output
    ColorChecker_All_GAMUT_WHITE-POINT_OETF.tiff : 24種類のColorCheckerを1枚の画像に収めたもの
    ColorChecker_Measure_Patch_GAMUT_WHITE-POINT_OETF_xx_NAME.tiff : 測定用パッチ
    ColorChecker_Value_GAMUT_WHITE-POINT_OETF.csv : xyY値およびRGB値を収めたCSVファイル

```

## Appendix

### A1. ColorChecker が複数ある件

なぜ ColorChecker が3種類も存在するかについては、BabelColor の [TechnicalPater](https://pdfs.semanticscholar.org/0e03/251ad1e6d3c3fb9cb0b1f9754351a959e065.pdf) が参考になる。</br>
※実を言うと x-rite が 2014年に新しいデータ(？)を公開しているが無視する。</br>
[カラーチェッカーSGおよびクラシックのチャートに適用される新しい仕様](http://xritephoto.com/ph_product_overview.aspx?ID=938&Action=Support&SupportID=5884)

### A2. ColorChecker 1976 と ColorChecker 2005 の違い

#### ColorChecker 1976

C光源での xyY が記載。D光源の値は無い

#### ColorChecker 2005

D光源での xyY値および L\*a\*b\*値が記載。GretagMacbeth が ColorChecker の値を D光源で測定し直したもの（らしい）。
