# KÜTÜPHANELER

from flask import Flask, render_template, flash, redirect, url_for, session, logging, request,make_response
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, FileField,PasswordField, IntegerField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "aracalsat"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "aracalsat"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

# decorator giriş
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın!","danger")
            return redirect(url_for("login"))
    return decorated_function

# KULLANICI KAYIT FORMU
class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.Length(min=4, max=25)])
    username = StringField("Kullanıcı Adı", validators=[validators.Length(min=5, max=35), validators.DataRequired(message="Lütfen kullanıcı adınızı girin!")])
    email = StringField("E-mail Adresi", validators=[validators.DataRequired(), validators.Email(message="Lütfen geçerli bir mail adresi girin!")])
    password = PasswordField("Parola", validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin!"),
        validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor!")
    ])
    confirm = PasswordField("Parolanızı tekrar giriniz")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifre")

# Anasayfa 
@app.route("/")
def index():
    return render_template("index.html")

# Kayıt olma 
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla kayıt oldunuz!","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)
    
# Giriş yapma
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE username = %s"
        result = cursor.execute(sorgu,(username,))
        
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız!","success")
                session["logged_in"] = True
                session["id"] = data["id"]
                session["username"] = username
                session["email"] = data["email"]
                session["name"] = data["name"]
                return redirect(url_for("index"))
            else:
                flash("Kullanıcı adı veya parolanızı yanlış girdiniz!","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor!","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html",form = form)

# logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
 
# DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM ads WHERE author_id = %s"
    result = cursor.execute(sorgu,(session["id"],))

    if result>0:
        ads = cursor.fetchall()
        sorgu2 = "SELECT favorites FROM users WHERE id=%s"
        cursor.execute(sorgu2,(session["id"],))
        data = cursor.fetchone()
        
        if data["favorites"] != "":
            favoritesId = (data["favorites"]).split()
            sql_sorgusu = "SELECT * FROM ads WHERE id IN ("
            for i, id in enumerate(favoritesId):
                if i != 0:
                    sql_sorgusu += ","
                sql_sorgusu += str(id)
            sql_sorgusu += ");"
            cursor.execute(sql_sorgusu)
            favorites = cursor.fetchall()
            return render_template("/dashboard.html",ads=ads,favorites=favorites)
        else:
            return render_template("/dashboard.html",ads=ads)
    else:
        return render_template("/dashboard.html")

# İLAN EKLEME
@app.route("/add",methods=["GET","POST"])
@login_required
def add():
    form = AddEkleme(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        city = form.city.data
        brand = form.brand.data
        model = form.model.data
        year = form.year.data
        context = form.context.data
        price = form.price.data
        images = form.images.data
        print(images)

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO ads(author,author_id,title,city,brand,model,year,context,price) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(sorgu,(session["name"],session["id"],title,city,brand,model,year,context,price))
        mysql.connection.commit()
        cursor.close()
        flash("İlan Başarıyla Eklendi!","success")
        return redirect(url_for("dashboard"))
    return render_template("/add.html",form=form)

# İLAN EKLEME FORM

class AddEkleme(Form):
    title = StringField("İlan Başlığı",validators=[validators.Length(min=5,max=100)])
    city = StringField("Şehir")
    brand = StringField("Marka")
    model = StringField("Model")
    year = IntegerField("Yıl")
    context = TextAreaField("Açıklama")
    price = IntegerField("Fiyat")
    images = FileField("Fotoğraf Ekleyin")
    

@app.route("/ads")
def ads():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM ads"
    result = cursor.execute(sorgu)

    if result > 0:
        ads = cursor.fetchall()
        return render_template("ads.html",ads=ads)
    else:
        return render_template("ads.html")
    
# İlan detayı sayfası

@app.route("/ad/<string:id>")
def ad(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM ads WHERE id=%s"
    result = cursor.execute(sorgu,(id,))
    
    if result > 0:
        ad = cursor.fetchone()
        return render_template("ad.html",ad=ad)
    else:
        return render_template("ad.html")

# İlan silme

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM ads WHERE author=%s and id=%s"
    result = cursor.execute(sorgu,(session["name"],id))

    if result>0:
        sorgu2 = "DELETE FROM ads WHERE id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("İlan silindi!","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir ilan yok veya bu işleme yetkiniz yok!","danger")
        return redirect(url_for("index"))
    
# İLAN GÜNCELLEME

@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM ads WHERE  id=%s and author=%s"
        result = cursor.execute(sorgu,(id,session["name"]))
        if result==0:
            flash("Böyle bir ilan yok veya bu işleme yetkiniz yok!","danger")
            return redirect(url_for("index"))
        else:
            ad = cursor.fetchone()
            form = AddEkleme()
            form.title.data = ad["title"]
            form.city.data = ad["city"]
            form.brand.data = ad["brand"]
            form.model.data = ad["model"]
            form.year.data = ad["year"]
            form.context.data = ad["context"]
            form.price.data = ad["price"]

            return render_template("update.html",form=form)
    else: # post request
        form = AddEkleme(request.form)
        newTitle = form.title.data
        newCity = form.city.data
        newBrand = form.brand.data
        newModel = form.model.data
        newYear = form.year.data
        newContext = form.context.data
        newPrice = form.price.data

        sorgu2 = "UPDATE ads SET title=%s,city=%s,brand=%s,model=%s,year=%s,context=%s,price=%s WHERE id=%s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newCity,newBrand,newModel,newYear,newContext,newPrice,id))
        mysql.connection.commit()
        flash("İlan başarıyla güncellendi!","success")
        return redirect(url_for("dashboard"))

# ARAMA KISMI
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM ads WHERE title LIKE '%"+ keyword +"%'"
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan kelimeye uygun ilan yok!","warning")
            return redirect(url_for("ads"))
        else:
            ads = cursor.fetchall()
            return render_template("ads.html",ads=ads)
        
@app.route("/about")
def about():
    return render_template("about.html")

# FAVORİ İLAN EKLEME

@app.route("/addfavorite/<string:id>")
@login_required
def addfavorite(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM ads WHERE author!=%s and id=%s"
    result = cursor.execute(sorgu,(session["name"],id))

    if result == 0:
        flash("Bu ilan zaten sizin olduğu için favoriye ekleyemezsiniz!","warning")
        return redirect(url_for("dashboard"))
    
    else:
        FavoriSorgusu = "SELECT favorites FROM users WHERE id=%s"
        cursor.execute(FavoriSorgusu,(session["id"],))
        favorites = cursor.fetchone()
        favorites = favorites["favorites"] # "3 4" 
        favorites = favorites.split(" ") # [3,4]
        if id in favorites:
            flash("Bu ilanı zaten daha önce favoriye eklediniz!","warning")
            return redirect(url_for("dashboard"))
        else:
            favorites.append(id)
            favorites = " ".join(favorites)

            FavoriEkleSorgusu = "UPDATE users SET favorites=%s WHERE id=%s"
            cursor.execute(FavoriEkleSorgusu,(favorites,session["id"]))
            mysql.connection.commit()
            cursor.close()
            flash("İlan Başarıyla Favorilerinize Eklendi!","success") 
            return redirect(url_for("dashboard"))
        
# FAVORİLERDEN KALDIR
@app.route("/delfromfav/<string:id>")
@login_required
def delfromfav(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT favorites FROM users WHERE id=%s"
    cursor.execute(sorgu,(session["id"],))
    favorites = cursor.fetchone()
    
    favorites = favorites["favorites"].split()

    if id not in favorites:
        flash("Bu ilan favori ilanlarınızdan birisi değil!","warning")
        return redirect(url_for("dashboard"))
    else:
        favorites.remove(id)

        favorites = " ".join(favorites)

        FavoriEkleSorgusu = "UPDATE users SET favorites=%s WHERE id=%s"
        cursor.execute(FavoriEkleSorgusu,(favorites,session["id"]))
        mysql.connection.commit()
        cursor.close()
        flash("İlan Başarıyla Favorilerinizden Kaldırıldı!","success") 
        return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)