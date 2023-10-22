import os, re, requests, shutil, time, random, subprocess
import img2pdf
from PIL import Image
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http
from googleapiclient.http import MediaFileUpload
import datetime

print(f"{datetime.datetime.utcnow()+datetime.timedelta(hours=9)}\nProgram started")
# 時間を0~10分程度ずらす
t = random.randint(0, 600)
print(f"Sleeping for {t} seconds.")
time.sleep(t)

credentials_file = "credential.json"
dl_path = "downloaded/"
referer = "https://kyuyokaitori.com/481"
url = "https://kyuyokaitori.com/wp-login.php?action=postpass"
post_password = ""
data = {'post_password': post_password,
        'Submit': '確定'}
upload_file = "output.pdf"

# ページにパスワードを入力する行為を模倣し、返り値からダウンロード用のurlと記事名を取得する
print("Getting the download url...")
res = requests.post(url,headers={'referer': referer}, data=data).text
article_title = re.sub(r'[\\/:*?"<>|]', '', re.findall(r'【(.*?)】', res)[0]).replace(' ', '_')
dl_url = re.findall(r'<a href="(.*?)\.zip"', res)[-1]+".zip"

# 取得したurlからzipファイルをダウンロード＆展開し、不要なフォルダなどを削除する。
print(f"Downloading the zip file from {dl_url}...")
filename = dl_url.split('/')[-1]
with open(dl_path+filename, mode="wb") as f:
    f.write(requests.get(dl_url).content)
subprocess.run(f"unzip -O UTF-8 {filename}", shell=True, cwd=f"{os.path.dirname(os.path.abspath(__file__))}/{dl_path}")
os.remove(dl_path+filename)
try:
    shutil.rmtree(dl_path+"__MACOSX")
except:
    pass

# 展開したファイルの一覧を取得し、それらを単一pdfとしてまとめる。
print("Converting img file to pdf...")
png_folder = dl_path+os.listdir(dl_path)[0]+"/"
try:
    os.remove(png_folder+".DS_Store")
except:
    pass
with open(upload_file, "wb") as f:
    f.write(img2pdf.convert([Image.open(png_folder+j).filename for j in sorted(os.listdir(png_folder), key=lambda s: int(re.search(r'\d+', s).group())) if j.lower().endswith((".png",".jpg","jpeg",".gif"))]))

# GoogleDriveにアップロードする。
print("Uploading the pdf file to drive...")
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credential.json', SCOPES)
http_auth = credentials.authorize(Http())
drive_service = build('drive', 'v3', http=http_auth)
media = MediaFileUpload(upload_file, mimetype='application/pdf', resumable=True)
file_metadata = {
    'name': (datetime.datetime.utcnow()+datetime.timedelta(hours=9)).strftime("%Y-%m-%d")+"_"+article_title,
    'mimeType': 'application/pdf',
    'parents': ['']
}
file = drive_service.files().create(body=file_metadata, media_body=media).execute()

# 後始末
shutil.rmtree(dl_path)
os.makedirs(dl_path, exist_ok=True)
print("All done!\n")