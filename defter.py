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