from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session, flash, send_file, jsonify
import os
import json
from datetime import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Güvenlik için önemli

# Kullanıcı veritabanı dosyası
USERS_FILE = 'users.json'
COMMENTS_FILE = 'comments.json'
FRIENDS_FILE = 'friends.json'
MESSAGES_FILE = 'messages.json'

# E-posta doğrulama fonksiyonu
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Kullanıcı veritabanını yükle
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            # Mevcut kullanıcıları güncelle
            for email, user in users.items():
                if 'profile_picture' not in user:
                    user['profile_picture'] = 'default_profile.png'
                if 'banner' not in user:
                    user['banner'] = 'default_banner.jpg'
                if 'bio' not in user:
                    user['bio'] = 'Henüz bir biyografi eklenmemiş.'
            return users
    return {}

# Kullanıcı veritabanını kaydet
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# Yorumları yükle
def load_comments():
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Yorumları kaydet
def save_comments(comments):
    with open(COMMENTS_FILE, 'w') as f:
        json.dump(comments, f)

# Kayıt olma sayfası
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Form doğrulama
        if not email or not username or not password or not confirm_password:
            flash('Lütfen tüm alanları doldurun.', 'error')
            return redirect(url_for('register'))
        
        if not is_valid_email(email):
            flash('Geçerli bir e-posta adresi girin.', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Şifreler eşleşmiyor.', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır.', 'error')
            return redirect(url_for('register'))
        
        if len(username) < 3:
            flash('Kullanıcı adı en az 3 karakter olmalıdır.', 'error')
            return redirect(url_for('register'))
        
        # Kullanıcı kontrolü
        users = load_users()
        if email in users:
            flash('Bu e-posta adresi zaten kayıtlı.', 'error')
            return redirect(url_for('register'))
        
        # Kullanıcı adı kontrolü
        for user in users.values():
            if user.get('username') == username:
                flash('Bu kullanıcı adı zaten kullanılıyor.', 'error')
                return redirect(url_for('register'))
        
        # Kullanıcıyı kaydet
        users[email] = {
            'username': username,
            'password': generate_password_hash(password),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'downloads': [],
            'friends': [],
            'comments': [],
            'profile_picture': 'default_profile.png',
            'banner': 'default_banner.jpg',
            'bio': 'Henüz bir biyografi eklenmemiş.'
        }
        save_users(users)
        
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Giriş sayfası
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        users = load_users()
        if email in users and check_password_hash(users[email]['password'], password):
            session['email'] = email
            session['username'] = users[email]['username']
            flash('Giriş başarılı!', 'success')
            return redirect(url_for('home'))
        
        flash('E-posta veya şifre hatalı.', 'error')
        return redirect(url_for('login'))
    
    return render_template('login.html')

# Çıkış yapma
@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('username', None)
    flash('Çıkış yapıldı.', 'success')
    return redirect(url_for('home'))

# Yorum ekleme
@app.route('/game/<int:game_id>/comment', methods=['POST'])
def add_comment(game_id):
    if 'email' not in session:
        flash('Yorum yapmak için giriş yapmalısınız.', 'error')
        return redirect(url_for('login'))
    
    comment_text = request.form.get('comment')
    if not comment_text:
        flash('Yorum boş olamaz.', 'error')
        return redirect(url_for('game_detail', game_id=game_id))
    
    comments = load_comments()
    if str(game_id) not in comments:
        comments[str(game_id)] = []
    
    comments[str(game_id)].append({
        'username': session['username'],
        'email': session['email'],
        'text': comment_text,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    save_comments(comments)
    flash('Yorumunuz başarıyla eklendi.', 'success')
    return redirect(url_for('game_detail', game_id=game_id))

# Basit veritabanı yerine sözlük kullanıyoruz
games = {
    1: {
        'id': 1,
        'title': 'DUSK',
        'description': 'Heyecan dolu bir macera oyunu. Yapımcı: David Szymanski (New Blood Interactive). Çıkış Tarihi: 10 Aralık 2018',
        'category': 'Macera',
        'image': 'DUSK.jpeg',
        'file': 'DUSK.zip',
        'size': '1.1 GB',
        'downloads': 0,
        'type': 'game'
    },
    2: {
        'id': 2,
        'title': 'ULTRAKILL',
        'description': 'Uzayda savaş ve keşif. Yapımcı: Arsi "Hakita" Patala (New Blood Interactive). Çıkış Tarihi: 3 Eylül 2020 (Erken Erişim)',
        'image': 'ULTRAKILL.jpg',
        'file': 'ULTRAKILL.zip',
        'size': '2.2 GB',
        'downloads': 0,
        'type': 'game'
    },
    3: {
        'id': 3,
        'title': 'Visual Studio Code',
        'description': 'Güçlü ve modern bir kod editörü. Yapımcı: Microsoft. Çıkış Tarihi: 29 Nisan 2015',
        'category': 'Geliştirme',
        'image': 'vscode.jpg',
        'file': 'VScode.zip',
        'size': '100 MB',
        'downloads': 0,
        'type': 'app',
        'screenshots': ['vscode1.jpg', 'vscode2.jpg', 'vscode3.jpg']
    },
    4: {
        'id': 4,
        'title': 'Discord',
        'description': 'Popüler iletişim uygulaması. Yapımcı: Jason Citron, Stanislav Vishnevskiy. Çıkış Tarihi: 13 Mayıs 2015',
        'category': 'İletişim',
        'image': 'discord.png',
        'file': 'discord.zip',
        'size': '150 MB',
        'downloads': 0,
        'type': 'app'
    },
    5: {
        'id': 5,
        'title': 'Spotify',
        'description': 'Müzik dinleme platformu. Yapımcı: Daniel Ek, Martin Lorentzon. Çıkış Tarihi: 7 Ekim 2008',
        'category': 'Müzik',
        'image': 'spotify.jpg',
        'file': 'spotify.zip',
        'size': '200 MB',
        'downloads': 0,
        'type': 'app'
    },
    6: {
        'id': 6,
        'title': 'Chrome',
        'description': 'Google tarafından geliştirilen web tarayıcısı. Yapımcı: Google. Çıkış Tarihi: 2 Eylül 2008',
        'category': 'İnternet',
        'image': 'chrome.jpg',
        'file': 'Crome.zip',
        'size': '120 MB',
        'downloads': 0,
        'type': 'app'
    },
    7: {
        'id': 7,
        'title': 'WhatsApp',
        'description': 'Popüler mesajlaşma uygulaması. Yapımcı: Jan Koum, Brian Acton. Çıkış Tarihi: 24 Şubat 2009',
        'category': 'İletişim',
        'image': 'whatsapp.png',
        'file': 'whatsAPP.zip',
        'size': '1.0 MB',
        'downloads': 0,
        'type': 'app'
    },
    8: {
        'id': 8,
        'title': 'Minecraft',
        'description': 'Popüler sandbox oyunu. Yapımcı: Markus "Notch" Persson (Mojang Studios). Çıkış Tarihi: 17 Mayıs 2009 (Alpha)',
        'category': 'Macera',
        'image': 'minecraft.jpg',
        'file': 'minecraft.zip',
        'size': '500 MB',
        'downloads': 0,
        'type': 'game'
    }
}

@app.route('/')
def home():
    return render_template('index.html', featured_games=list(games.values())[:4])

@app.route('/games')
def all_games():
    games_list = [game for game in games.values() if game['type'] == 'game']
    return render_template('games.html', games=games_list, title='Oyunlar')

@app.route('/apps')
def all_apps():
    apps_list = [game for game in games.values() if game['type'] == 'app']
    return render_template('games.html', games=apps_list, title='Uygulamalar')

@app.route('/game/<int:game_id>')
def game_detail(game_id):
    game = games.get(game_id)
    if not game:
        return redirect(url_for('all_games'))
    
    comments = load_comments()
    game_comments = comments.get(str(game_id), [])
    
    return render_template('game_detail.html', game=game, comments=game_comments)

@app.route('/download/<int:game_id>')
def download_game(game_id):
    game = games.get(game_id)
    if not game:
        return redirect(url_for('all_games'))
    
    # Kullanıcı girişi kontrolü
    if 'email' not in session:
        flash('İndirmek için giriş yapmalısınız.', 'error')
        return redirect(url_for('login'))
    
    # İndirme sayısını artır
    games[game_id]['downloads'] += 1
    
    # Kullanıcının indirme geçmişini güncelle
    users = load_users()
    if session['email'] in users:
        users[session['email']]['downloads'].append({
            'game_id': game_id,
            'title': game['title'],
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        save_users(users)
    
    # WhatsApp için özel dosya yolu
    if game['title'] == 'WhatsApp':
        return send_from_directory(
            'static/games',
            'whatsAPP.zip',
            as_attachment=True,
            download_name='WhatsAppSetup.exe'
        )
    
    # VSCode için özel dosya yolu
    if game['title'] == 'Visual Studio Code':
        return send_from_directory(
            'static/games',
            'VScode.zip',
            as_attachment=True,
            download_name='VSCodeSetup.zip'
        )
    
    # Discord için özel dosya yolu
    if game['title'] == 'Discord':
        return send_from_directory(
            'static/games',
            'discord.zip',
            as_attachment=True,
            download_name='DiscordSetup.exe'
        )
    
    # Chrome için özel dosya yolu
    if game['title'] == 'Chrome':
        return send_from_directory(
            'static/games',
            'Crome.zip',
            as_attachment=True,
            download_name='ChromeSetup.exe'
        )
    
    # Spotify için özel dosya yolu
    if game['title'] == 'Spotify':
        return send_from_directory(
            'static/games',
            'spotify.zip',
            as_attachment=True,
            download_name='SpotifySetup.exe'
        )
    
    # Minecraft için özel dosya yolu
    if game['title'] == 'Minecraft':
        return send_from_directory(
            'static/games',
            'minecraft.zip',
            as_attachment=True,
            download_name='MinecraftSetup.exe'
        )
    
    return send_from_directory(
        'static/games',
        game['file'],
        as_attachment=True
    )

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    results = [game for game in games.values() if query in game['title'].lower()]
    return render_template('search.html', results=results, query=query)

# Arkadaşlık isteği gönderme
@app.route('/send_friend_request/<username>')
def send_friend_request(username):
    if 'email' not in session:
        flash('Bu işlem için giriş yapmalısınız.', 'error')
        return redirect(url_for('login'))
    
    current_user = session['email']
    friends = load_friends()
    
    # Kendine istek göndermeyi engelle
    users = load_users()
    if users[current_user]['username'] == username:
        flash('Kendinize arkadaşlık isteği gönderemezsiniz.', 'error')
        return redirect(url_for('profile', username=username))
    
    # İstek zaten gönderilmiş mi kontrol et
    if current_user in friends and username in friends[current_user]['sent_requests']:
        flash('Bu kullanıcıya zaten arkadaşlık isteği gönderdiniz.', 'error')
        return redirect(url_for('profile', username=username))
    
    # İstek gönder
    if current_user not in friends:
        friends[current_user] = {'sent_requests': [], 'received_requests': [], 'friends': []}
    
    friends[current_user]['sent_requests'].append(username)
    
    # Alıcının verilerini güncelle
    receiver_email = None
    for email, user in users.items():
        if user['username'] == username:
            receiver_email = email
            break
    
    if receiver_email:
        if receiver_email not in friends:
            friends[receiver_email] = {'sent_requests': [], 'received_requests': [], 'friends': []}
        friends[receiver_email]['received_requests'].append(users[current_user]['username'])
    
    save_friends(friends)
    flash('Arkadaşlık isteği gönderildi.', 'success')
    return redirect(url_for('profile', username=username))

# Arkadaşlık isteğini kabul etme
@app.route('/accept_friend_request/<username>')
def accept_friend_request(username):
    if 'email' not in session:
        flash('Bu işlem için giriş yapmalısınız.', 'error')
        return redirect(url_for('login'))
    
    current_user = session['email']
    friends = load_friends()
    users = load_users()
    
    # İsteği kabul et
    if username in friends[current_user]['received_requests']:
        friends[current_user]['received_requests'].remove(username)
        friends[current_user]['friends'].append(username)
        
        # Gönderenin verilerini güncelle
        sender_email = None
        for email, user in users.items():
            if user['username'] == username:
                sender_email = email
                break
        
        if sender_email:
            friends[sender_email]['sent_requests'].remove(users[current_user]['username'])
            friends[sender_email]['friends'].append(users[current_user]['username'])
        
        save_friends(friends)
        flash('Arkadaşlık isteği kabul edildi.', 'success')
    
    return redirect(url_for('profile', username=username))

# Arkadaşlık isteğini reddetme
@app.route('/reject_friend_request/<username>')
def reject_friend_request(username):
    if 'email' not in session:
        flash('Bu işlem için giriş yapmalısınız.', 'error')
        return redirect(url_for('login'))
    
    current_user = session['email']
    friends = load_friends()
    users = load_users()
    
    # İsteği reddet
    if username in friends[current_user]['received_requests']:
        friends[current_user]['received_requests'].remove(username)
        
        # Gönderenin verilerini güncelle
        sender_email = None
        for email, user in users.items():
            if user['username'] == username:
                sender_email = email
                break
        
        if sender_email:
            friends[sender_email]['sent_requests'].remove(users[current_user]['username'])
        
        save_friends(friends)
        flash('Arkadaşlık isteği reddedildi.', 'success')
    
    return redirect(url_for('profile', username=username))

# Mesaj gönderme
@app.route('/send_message/<username>', methods=['POST'])
def send_message(username):
    if 'email' not in session:
        flash('Bu işlem için giriş yapmalısınız.', 'error')
        return redirect(url_for('login'))
    
    current_user = session['email']
    message_text = request.form.get('message')
    
    if not message_text:
        flash('Mesaj boş olamaz.', 'error')
        return redirect(url_for('profile', username=username))
    
    messages = load_messages()
    users = load_users()
    
    # Mesajı kaydet
    if current_user not in messages:
        messages[current_user] = {}
    
    receiver_email = None
    for email, user in users.items():
        if user['username'] == username:
            receiver_email = email
            break
    
    if receiver_email:
        if receiver_email not in messages[current_user]:
            messages[current_user][receiver_email] = []
        
        messages[current_user][receiver_email].append({
            'sender': users[current_user]['username'],
            'receiver': username,
            'text': message_text,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Alıcının mesajlarını da güncelle
        if receiver_email not in messages:
            messages[receiver_email] = {}
        if current_user not in messages[receiver_email]:
            messages[receiver_email][current_user] = []
        
        messages[receiver_email][current_user].append({
            'sender': users[current_user]['username'],
            'receiver': username,
            'text': message_text,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        save_messages(messages)
        flash('Mesajınız gönderildi.', 'success')
    
    return redirect(url_for('profile', username=username))

# Profil sayfası
@app.route('/profile/<username>')
def profile(username):
    if 'email' not in session:
        flash('Bu sayfayı görüntülemek için giriş yapmalısınız.', 'error')
        return redirect(url_for('login'))
    
    users = load_users()
    friends = load_friends()
    messages = load_messages()
    
    # Kullanıcıyı bul
    user_email = None
    for email, user in users.items():
        if user.get('username') == username:  # get() kullanarak güvenli erişim
            user_email = email
            break
    
    if not user_email:
        flash('Kullanıcı bulunamadı.', 'error')
        return redirect(url_for('home'))
    
    # Kullanıcı verilerini güvenli bir şekilde al
    user_data = users[user_email]
    if not user_data.get('friends'):
        user_data['friends'] = []
    if not user_data.get('comments'):
        user_data['comments'] = []
    
    # Arkadaşlık durumunu kontrol et
    current_user = session['email']
    friendship_status = None
    
    if current_user in friends:
        if username in friends[current_user].get('friends', []):
            friendship_status = 'friends'
        elif username in friends[current_user].get('sent_requests', []):
            friendship_status = 'request_sent'
        elif username in friends[current_user].get('received_requests', []):
            friendship_status = 'request_received'
    
    # Mesajları getir
    user_messages = []
    if current_user in messages and user_email in messages[current_user]:
        user_messages = messages[current_user][user_email]
    
    return render_template('profile.html',
                         user=user_data,
                         friendship_status=friendship_status,
                         messages=user_messages)

# Arkadaşları yükle
def load_friends():
    if os.path.exists(FRIENDS_FILE):
        with open(FRIENDS_FILE, 'r') as f:
            return json.load(f)
    # Dosya yoksa boş bir sözlük oluştur ve kaydet
    friends = {}
    save_friends(friends)
    return friends

# Arkadaşları kaydet
def save_friends(friends):
    with open(FRIENDS_FILE, 'w') as f:
        json.dump(friends, f)

# Mesajları yükle
def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    # Dosya yoksa boş bir sözlük oluştur ve kaydet
    messages = {}
    save_messages(messages)
    return messages

# Mesajları kaydet
def save_messages(messages):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f)

# Dosya yükleme ayarları
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/update_profile_picture', methods=['POST'])
def update_profile_picture():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Oturum açmanız gerekiyor'})
    
    if 'profile' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
    
    file = request.files['profile']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', unique_filename))
        
        # Kullanıcı verilerini güncelle
        users = load_users()
        for user in users:
            if user['email'] == session['email']:
                user['profile_picture'] = unique_filename
                break
        
        save_users(users)
        return jsonify({'success': True, 'new_url': f"/static/images/profiles/{unique_filename}"})
    
    return jsonify({'success': False, 'message': 'Geçersiz dosya formatı'})

@app.route('/update_banner', methods=['POST'])
def update_banner():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Oturum açmanız gerekiyor'})
    
    if 'banner' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
    
    file = request.files['banner']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'banners', unique_filename))
        
        # Kullanıcı verilerini güncelle
        users = load_users()
        for user in users:
            if user['email'] == session['email']:
                user['banner'] = unique_filename
                break
        
        save_users(users)
        return jsonify({'success': True, 'new_url': f"/static/images/banners/{unique_filename}"})
    
    return jsonify({'success': False, 'message': 'Geçersiz dosya formatı'})

@app.route('/update_bio', methods=['POST'])
def update_bio():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Oturum açmanız gerekiyor'})
    
    data = request.get_json()
    new_bio = data.get('bio', '')
    
    if new_bio:
        users = load_users()
        for user in users:
            if user['email'] == session['email']:
                user['bio'] = new_bio
                break
        
        save_users(users)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Biyografi boş olamaz'})

if __name__ == '__main__':
    app.run(debug=True)