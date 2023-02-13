import os
import sys
import subprocess
import datetime
from yt_dlp import YoutubeDL
from webdav3.client import Client

dt_now = datetime.datetime.now()

dav_user = os.environ['DAV_USER']
dav_password = os.environ['DAV_PASS']
dav_server = os.environ['DAV_SERVER']

# WebDAVのオプション類設定
options = {
    'webdav_hostname': dav_server + "remote.php/dav/files/" + dav_user + "/",
    'webdav_login':    dav_user,
    'webdav_password': dav_password
}
client = Client(options)
# client.verify = False # To not check SSL certificates (Default = True)

# WebDAV上のurl格納ファイル場所
remotepath='nextload/url.txt'
# local上のurl格納ファイル場所
localpath='./url.txt'

# urlファイルからurlを取り出す関数
# 戻り値：string url
def parseurl(urlfile):
    # ファイルをオープンする
    with open(urlfile, 'r') as f:
        # 一行読む
        url = f.read().split("\n")
    return url[0]

# 縮小版videoファイル作成関数
# 戻り値：string outputしたファイル名
def ffmpeg_cnv_minivideo(inputfilename , outputfilename):
    # ffmpegコマンドライン文字列作成
    cmd = 'ffmpeg -y -vaapi_device /dev/dri/renderD128 -i "{0}" -vf \'hwupload,scale_vaapi=w=-2:h=720:format=nv12\' -c:v h264_vaapi -qp 25 -c:a libfdk_aac -b:a 192k "{1}"'.format(inputfilename , outputfilename)
    # コマンドを実行する
    subprocess.run(cmd, shell=True)
    return outputfilename

# 音声ファイル作成関数
# 戻り値：string outputしたファイル名
def ffmpeg_cnv_audio(inputfilename , outputfilename):
    # ffmpegコマンドライン文字列作成
    cmd = 'ffmpeg -y -i "{0}" -vn -c:a libfdk_aac -b:a 192k "{1}"'.format(inputfilename , outputfilename)
    # コマンドを実行する
    subprocess.run(cmd, shell=True)
    return outputfilename

# 動画ダウンロード関数
# 戻り値：string downloadしたファイル名
def dlfile(url):
    # ダウンロード条件を設定する。今回は画質・音質ともに最高の動画をダウンロードする
    ydl_opts = {'format': 'bestvideo+bestaudio/best',
                # ファイル名を動画IDにする場合以下のコメントを外す。
                # 'outtmpl': '%(id)s.%(ext)s',
                }
    # オプションの引き渡し
    with YoutubeDL(ydl_opts) as ydl:
        # urlから動画[情報]をダウンロード
        result = ydl.extract_info(url, download=False)
        # resultからダウンロードファイル名を取得
        filename = ydl.prepare_filename(result)
        # ファイル存在確認
        is_file = os.path.isfile(filename)
        if not is_file:
            # urlから動画をダウンロード
            result = ydl.extract_info(url, download=True)
    return filename

# WebDAVアップロード関数
def uploadfile(remotepath,localpath):
    # WebDAV上に同じファイル名が無ければ
    if not client.check(remotepath):
        # アップロード開始
        print("Upload!")
        client.upload(remotepath,localpath)

# videoアップロード変数生成
def uploadvideofile(filename):
    # 格納先パスの生成
    remotepath="nextload/videos/" + filename
    # 格納元パスの生成
    localpath="./" + filename
    uploadfile(remotepath,localpath)

# audioアップロード変数生成
def uploadaudiofile(filename):
    # 格納先パスの生成
    remotepath="nextload/audios/" + filename
    # 格納元パスの生成
    localpath="./" + filename
    uploadfile(remotepath,localpath)

# Videoファイル生成関数
# 戻り値：string コンバート後のファイル名
def cnvvideo(filename):
    # ファイル名と拡張子を取得
    filebase = os.path.splitext(os.path.basename(filename))[0]
    extname  = os.path.splitext(filename)
    # 拡張子を小文字に揃える
    lowerext = extname[1].lower()
    # 元ファイルはmp4か？
    if lowerext =='.mp4':
        # Yes 出力ファイル名に_miniを追加
        outputfile = filebase + '_mini.mp4'
    else:
        # No 出力ファイル名をMP4にセット
        outputfile = filebase + '.mp4'
    # エンコード開始
    ffmpeg_cnv_minivideo(filename,outputfile)
    # 動画ファイル名を返す
    return outputfile

# Audioファイル生成関数
# 戻り値：string コンバート後のファイル名
def cnvaudio(filename):
    # ファイル名と拡張子を取得
    filebase = os.path.splitext(os.path.basename(filename))[0]
    extname  = os.path.splitext(filename)
    # 出力ファイル名生成
    outputfile = filebase + '.m4a'
    # 音声ファイル作成
    ffmpeg_cnv_audio(filename,outputfile)
    # 音声ファイル名を返す
    return outputfile
#
# メイン処理
#
# WebDAVにurl格納ファイルはあるか？
if client.check(remotepath):
    print(dt_now)
    print("Download Start!")
    # コンテンツのurlをdownload
    client.download(remotepath,localpath)
    # コンテンツのurlを解析
    url = parseurl(localpath)
    # ダウンロード開始。戻り値はダウンロード後のファイル名
    filename = dlfile(url)
    # 元コンテンツのアップロード
    uploadvideofile(filename)
    # 縮小版を作成
    retname = cnvvideo(filename)
    # 縮小版をアップロード
    uploadvideofile(retname)
    # 音声のみのファイル作成
    retname = cnvaudio(filename)
    # 音声をアップロード
    uploadaudiofile(retname)
    # 完了したのでurlを削除
    client.clean(remotepath)
    dt_now = datetime.datetime.now()
    print(dt_now)
