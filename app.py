"""Aniro - anime wallpaper manager for Windows."""
import ctypes, json, os, sys, threading, uuid
from pathlib import Path
import requests
from PIL import Image
from PySide6.QtCore import Qt, QObject, Signal, QThread
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QFrame,QVBoxLayout,QHBoxLayout,QLabel,
    QPushButton,QLineEdit,QComboBox,QListWidget,QListWidgetItem,QFileDialog,QMessageBox,QGraphicsDropShadowEffect)
from PySide6.QtGui import QColor

ASSET_DIR=Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
LOGO=ASSET_DIR/"logo.png"
ROOT=Path(os.getenv("APPDATA",str(Path.home())))/"Aniro"
ROOT.mkdir(parents=True,exist_ok=True)
FAV=ROOT/"favorites.json"
CACHE=ROOT/"cache"
CACHE.mkdir(exist_ok=True)
API="https://wallhaven.cc/api/v1/search"
CSS="""QWidget{background:#080f20;color:#e8f4ff;font:13px 'Segoe UI'}
QLineEdit,QComboBox,QListWidget{background:#101f38;border:1px solid #315378;border-radius:13px;padding:10px}
QPushButton{background:#19365d;border:1px solid #3d6794;border-radius:12px;padding:11px;font-weight:600}
QPushButton:hover{background:#285a95} QPushButton:disabled{color:#667e9d;background:#132038}
QFrame#dock{background:rgba(37,65,111,215);border:1px solid rgba(130,210,255,140);border-radius:26px}
QFrame#dock QPushButton{background:rgba(255,255,255,16);border:1px solid rgba(255,255,255,30);border-radius:18px;padding:13px 22px}
QFrame#dock QPushButton:hover{background:rgba(94,175,255,100)}
QFrame#dock QPushButton[active="true"]{background:rgba(75,160,255,140);border:1px solid #8cddff}"""

class Worker(QObject):
    done=Signal(object)
    failed=Signal(str)
    finished=Signal()
    def __init__(self,fn):
        super().__init__();self.fn=fn
    def run(self):
        try:self.done.emit(self.fn())
        except Exception as e:self.failed.emit(str(e))
        finally:self.finished.emit()

def image_bytes(url):
    if url.startswith("file://"):return Path(url[7:]).read_bytes()
    if Path(url).is_file():return Path(url).read_bytes()
    r=requests.get(url,timeout=30,headers={"User-Agent":"Aniro/1.0"});r.raise_for_status()
    if not r.headers.get("content-type","").startswith("image/"):raise ValueError("Not an image")
    if len(r.content)>35*1024*1024:raise ValueError("Image too large")
    return r.content

class Aniro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aniro");self.resize(1160,780);self.setMinimumSize(850,590)
        if LOGO.is_file():self.setWindowIcon(QIcon(str(LOGO)))
        self.items=[];self.selected=None;self.threads=[]
        try:self.favorites=json.loads(FAV.read_text(encoding="utf-8"))
        except (OSError,ValueError):self.favorites=[]
        root=QWidget();self.setCentralWidget(root)
        main=QVBoxLayout(root);main.setContentsMargins(28,20,28,16);main.setSpacing(14)
        top=QHBoxLayout()
        brand=QLabel("ANIRO");brand.setStyleSheet("color:#70d1ff;font-size:25px;font-weight:900;letter-spacing:3px")
        if LOGO.is_file():
            logo=QLabel();logo.setFixedSize(48,48)
            logo.setPixmap(QPixmap(str(LOGO)).scaled(48,48,Qt.KeepAspectRatio,Qt.SmoothTransformation))
            top.addWidget(logo)
        top.addWidget(brand);top.addStretch()
        self.title=QLabel("Discover wallpapers");self.title.setStyleSheet("font-size:20px;font-weight:700")
        top.addWidget(self.title);main.addLayout(top)
        self.filters=QWidget();searchrow=QHBoxLayout(self.filters);searchrow.setContentsMargins(0,0,0,0)
        self.query=QLineEdit();self.query.setPlaceholderText("Search anime, characters, moods...")
        self.query.returnPressed.connect(self.search);searchrow.addWidget(self.query,1)
        self.res=QComboBox();self.res.addItems(["All resolutions","1920x1080","2560x1440","3840x2160"])
        searchrow.addWidget(self.res)
        self.searchbtn=QPushButton("Search");self.searchbtn.clicked.connect(self.search);searchrow.addWidget(self.searchbtn)
        main.addWidget(self.filters);self.filters.hide()
        self.status=QLabel("Discover anime wallpapers or import an image")
        self.status.setStyleSheet("color:#93b3d5");main.addWidget(self.status)
        body=QHBoxLayout();body.setSpacing(18)
        self.listing=QListWidget();self.listing.currentRowChanged.connect(self.select);body.addWidget(self.listing,2)
        side=QVBoxLayout()
        self.preview=QLabel("Select a wallpaper to preview");self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(320,280);self.preview.setWordWrap(True)
        self.preview.setStyleSheet("background:#10203a;border:1px solid #31547c;border-radius:16px")
        side.addWidget(self.preview,1)
        self.info=QLabel("");side.addWidget(self.info)
        self.applybtn=QPushButton("Set as desktop wallpaper");self.applybtn.clicked.connect(self.apply);side.addWidget(self.applybtn)
        self.heart=QPushButton("♡ Add to favorites");self.heart.clicked.connect(self.toggle);side.addWidget(self.heart)
        self.savebtn=QPushButton("Download / Save image");self.savebtn.clicked.connect(self.save);side.addWidget(self.savebtn)
        body.addLayout(side,3);main.addLayout(body,1)
        row=QHBoxLayout();row.addStretch()
        dock=QFrame();dock.setObjectName("dock");bar=QHBoxLayout(dock);bar.setContentsMargins(10,9,10,9)
        self.nav={}
        for name,icon,action in [("Wallpapers","✦",self.wallpapers),("Favorites","♥",self.show_favorites),
                                 ("Search","⌕",self.show_search),("Import","+",self.import_image)]:
            btn=QPushButton(icon+"  "+name);btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(action);bar.addWidget(btn);self.nav[name]=btn
        glow=QGraphicsDropShadowEffect(dock);glow.setBlurRadius(38);glow.setOffset(0,7)
        glow.setColor(QColor(22,118,241,110));dock.setGraphicsEffect(glow)
        row.addWidget(dock);row.addStretch();main.addLayout(row)
        self.activate("Wallpapers");self.buttons();self.search()

    def activate(self,name):
        for key,btn in self.nav.items():
            btn.setProperty("active","true" if key==name else "false")
            btn.style().unpolish(btn);btn.style().polish(btn)
    def wallpapers(self):
        self.activate("Wallpapers");self.filters.hide();self.title.setText("Discover wallpapers");self.search()
    def show_search(self):
        self.activate("Search");self.filters.show();self.title.setText("Search wallpapers");self.query.setFocus()
    def show_favorites(self):
        self.activate("Favorites");self.filters.hide();self.title.setText("Your favorites")
        self.items=list(self.favorites);self.populate();self.status.setText(str(len(self.items))+" favorites")
    def run_job(self,fn,done):
        worker=Worker(fn);thread=QThread(self);worker.moveToThread(thread)
        thread.started.connect(worker.run);worker.done.connect(done);worker.failed.connect(self.error)
        worker.finished.connect(thread.quit);worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda:self.threads.remove(thread) if thread in self.threads else None)
        self.threads.append(thread);thread.start()
    def error(self,msg):
        self.searchbtn.setEnabled(True);self.status.setText("Error: "+msg)
        QMessageBox.warning(self,"Aniro",msg)
    def search(self):
        q=self.query.text().strip() or "anime";resolution=self.res.currentText()
        self.searchbtn.setEnabled(False);self.status.setText("Finding wallpapers...")
        def fetch():
            params={"q":q,"categories":"010","purity":"100","sorting":"relevance"}
            if resolution!="All resolutions":params["atleast"]=resolution
            r=requests.get(API,params=params,timeout=25);r.raise_for_status()
            return [{"id":x["id"],"name":x["id"],"resolution":x.get("resolution",""),
                "preview":x.get("thumbs",{}).get("large",""),"url":x["path"]} for x in r.json().get("data",[])]
        def done(items):
            self.searchbtn.setEnabled(True);self.items=items;self.populate()
            self.status.setText(str(len(items))+" wallpapers found")
        self.run_job(fetch,done)
    def populate(self):
        self.listing.clear();self.selected=None;self.preview.clear()
        self.preview.setText("Select a wallpaper to preview")
        self.info.setText("")
        for item in self.items:
            self.listing.addItem(("♥ " if self.is_fav(item) else "")+item["name"]+"  •  "+item.get("resolution",""))
        self.buttons()
    def is_fav(self,item):return any(x["id"]==item["id"] for x in self.favorites)
    def select(self,index):
        self.selected=self.items[index] if 0<=index<len(self.items) else None
        self.buttons()
        if not self.selected:return
        item=self.selected;self.info.setText(item["name"]+" · "+item.get("resolution",""))
        self.preview.setText("Loading preview...")
        def done(data):
            if self.selected is not item:return
            pix=QPixmap()
            if pix.loadFromData(data):
                self.preview.setPixmap(pix.scaled(570,420,Qt.KeepAspectRatio,Qt.SmoothTransformation))
            else:self.preview.setText("Preview unavailable")
        self.run_job(lambda:image_bytes(item.get("preview") or item["url"]),done)
    def buttons(self):
        for btn in [self.applybtn,self.heart,self.savebtn]:btn.setEnabled(self.selected is not None)
        if self.selected:self.heart.setText("♥ Remove from favorites" if self.is_fav(self.selected) else "♡ Add to favorites")
    def toggle(self):
        if not self.selected:return
        if self.is_fav(self.selected):
            self.favorites=[x for x in self.favorites if x["id"]!=self.selected["id"]]
        else:self.favorites.append(dict(self.selected))
        FAV.write_text(json.dumps(self.favorites,indent=2,ensure_ascii=False),encoding="utf-8")
        if self.nav["Favorites"].property("active")=="true":self.show_favorites()
        else:
            row=self.listing.currentRow()
            if row>=0:
                x=self.selected;self.listing.item(row).setText(("♥ " if self.is_fav(x) else "")+x["name"]+"  •  "+x.get("resolution",""))
        self.buttons()
    def local(self,item):
        if item.get("local"):return Path(item["url"])
        suffix=Path(item["url"].split("?")[0]).suffix.lower()
        if suffix not in (".jpg",".jpeg",".png",".webp"):suffix=".jpg"
        path=CACHE/("wallpaper_"+item["id"]+suffix)
        if not path.exists():path.write_bytes(image_bytes(item["url"]))
        return path
    def apply(self):
        if not self.selected:return
        item=dict(self.selected);self.status.setText("Applying wallpaper...")
        def task():
            if sys.platform!="win32":raise RuntimeError("Windows only")
            bmp=CACHE/"desktop.bmp"
            with Image.open(self.local(item)) as im:im.convert("RGB").save(bmp,"BMP")
            if not ctypes.windll.user32.SystemParametersInfoW(20,0,str(bmp),3):raise ctypes.WinError()
            return True
        self.run_job(task,lambda _:self.status.setText("Wallpaper applied successfully!"))
    def save(self):
        if not self.selected:return
        item=dict(self.selected)
        target,_=QFileDialog.getSaveFileName(self,"Save wallpaper",str(Path.home()/"Pictures"/(item["id"]+".jpg")),"Images (*.jpg *.png *.webp)")
        if not target:return
        def task():
            with Image.open(self.local(item)) as im:
                fmt={".png":"PNG",".webp":"WEBP"}.get(Path(target).suffix.lower(),"JPEG")
                im.convert("RGB").save(target,fmt)
            return target
        self.run_job(task,lambda path:self.status.setText("Saved: "+path))
    def import_image(self):
        path,_=QFileDialog.getOpenFileName(self,"Import image",str(Path.home()),"Images (*.jpg *.jpeg *.png *.webp *.bmp)")
        if not path:return
        try:
            with Image.open(path) as im:res=f"{im.width}x{im.height}"
        except Exception as e:self.error(str(e));return
        self.activate("Import");self.filters.hide();self.title.setText("Imported image")
        self.items=[{"id":"local:"+path,"name":Path(path).name,"resolution":res,"preview":path,"url":path,"local":True}]
        self.populate();self.listing.setCurrentRow(0);self.status.setText("Image ready to use")

if __name__=="__main__":
    app=QApplication(sys.argv);app.setStyleSheet(CSS)
    window=Aniro();window.show();sys.exit(app.exec())
