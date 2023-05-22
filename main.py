# KÜTÜPHANELER

from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, IntegerField, validators
from passlib.hash import sha256_crypt
from functools import wraps

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


app = Flask(__name__)
app.secret_key = "aracalsat"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "aracalsat"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

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
    return render_template("/dashboard.html")

# İLAN EKLEME
@app.route("/add",methods=["GET","POST"])
@login_required
def add():
    form = AddEkleme(request.form)



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
    

@app.route("/ads/<string:id>")

def detail(id):
    return "Article Id:" + id

if __name__ == "__main__":
    app.run(debug=True)