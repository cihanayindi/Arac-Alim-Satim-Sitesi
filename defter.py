# FOTOĞRAF EKLEME

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/deneme', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            
            filedata = base64.b64encode(file.read()).decode('utf-8')
            
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO files (filename, filedata) VALUES (%s, %s)",(file.filename, filedata))
            mysql.connection.commit()
            cursor.close()
            
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index', name=filename))
        
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

@app.route('/download/<string:image_id>', methods=['GET'])
def download(image_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT filename, filedata FROM files WHERE id = %s", (image_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return render_template("deneme2.html",filedata = result["filedata"],filename = result["filename"])
    else:
        return "Image not found"

# def send_image(data, filename):
#     response = make_response(data)
#     response.headers['Content-Type'] = 'image/jpeg'  # Eğer resim dosyası JPEG ise, content type'ı buna göre ayarlayın
#     response.headers['Content-Disposition'] = f'attachment; filename={filename}'
#     return response

# DURSUN