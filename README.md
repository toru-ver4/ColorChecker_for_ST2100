# ITU-R BT.2100 向け ColorChecker 作成

## 概要

SDR の ColorChecker は RGB値が様々な場所で公開されているが、
HDR の ColorChecker の RGB値は調べる限りではどこにも公開されていないので作る。

余談だが、本ドキュメントでは*マクベスチャート*という呼び方はせず、*ColorChecker*に名称を統一する。理由は Wikipedia での本件の項目名が ColorChecker だったからである。

## ColorChekcr の色座標データ

BabelColor が公開している [ColorChecker RGB and spectra](http://www.babelcolor.com/download/ColorChecker_RGB_and_spectra.xls) を使用する。

このファイルでは以下の3種類の ColorChecker のデータが公開されている。

* BabelColor Avg
* ColorChecker 2005
* ColorChecker 1976

今回は *ColorChecker 2005* を用いる。理由は何となくである。別のを使いたければ後述のソースコードを1行修正すれば良い。

### 余談1：ColorChecker が複数ある件

末尾の Appendix1 参照。

なぜ ColorChecker が3種類も存在するかについては、BabelColor の [TechnicalPater](https://pdfs.semanticscholar.org/0e03/251ad1e6d3c3fb9cb0b1f9754351a959e065.pdf) が参考になる。</br>
※実を言うと x-rite が 2014年に新しいデータ(？)を公開しているが無視する。</br>
[カラーチェッカーSGおよびクラシックのチャートに適用される新しい仕様](http://xritephoto.com/ph_product_overview.aspx?ID=938&Action=Support&SupportID=5884)



## ColorChecker の色温度変換

公開されている ColorChecker の xyY値 は D50光源の値である。一般的なディスプレイは D65 で表示するため D50 → D65 の変換が必要となる。

色温度変換の際には *chromatic adaptation* と呼ばれる補正？をするのが一般的である。変換方式として広く使われているのは *Bradford* 方式であるが、今回は *CAT02* 方式を使用する。

理由は２つ。

* CAT02方式は ACES での色温度変換で使用可能である(Bradford か CAT02 か選択可能)
* 某社のカメラの IDT を調べたところ、CAT02方式で変換Matrixが計算されていた

もちろん、Bradford変換をしたい場合は、後述のソースコードを1行修正すれば実現できる。

## 実装

```main.py``` 参照。

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

```text

./output/rgb_value

```

## Appendix

### Appendix1. ColorChecker が複数ある件

なぜ ColorChecker が3種類も存在するかについては、BabelColor の [TechnicalPater](https://pdfs.semanticscholar.org/0e03/251ad1e6d3c3fb9cb0b1f9754351a959e065.pdf) が参考になる。</br>
※実を言うと x-rite が 2014年に新しいデータ(？)を公開しているが無視する。</br>
[カラーチェッカーSGおよびクラシックのチャートに適用される新しい仕様](http://xritephoto.com/ph_product_overview.aspx?ID=938&Action=Support&SupportID=5884)

### Appendix2. ColorChecker 1976 と 2005 の違い

#### ColorChecker 1976

C光源での xyY が記載。D光源の値は無い

#### ColorChecker 2005

D光源での xyY値および L\*a\*b\*値が記載。GretagMacbeth が ColorChecker の値を D光源で測定し直したもの（らしい）。


## 実装前のメモ

### CSV仕様

idx, name, x, y, Y, R, G, B
