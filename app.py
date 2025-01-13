from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    
    user = db.relationship('User')
    menu_item = db.relationship('MenuItem')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('admin' if user.role == 'admin' else 'user'))

    # return redirect(url_for('index'))   th
    return render_template('index.html')

@app.route('/user')
@login_required
def user():
    if current_user.role != 'user':
        return redirect(url_for('index'))

    menu_items = MenuItem.query.all()
    orders = Order.query.filter_by(user_id=current_user.id).all()     
    #i can write current_user.orders but for that i have to define relationship as user = db.relationship('User', backref=db.backref('orders', lazy=True))
    return render_template('user.html', menu_items=menu_items, orders=orders)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    menu_items = MenuItem.query.all()
    return render_template('admin.html', menu_items=menu_items)


@app.route('/admin/menu', methods=['GET', 'POST'])
@login_required
def add_menu_item():
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        price = request.form['price']

        if not name or not price:
            return redirect(url_for('admin'))

        new_item = MenuItem(name=name, description=description, price=price)
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('admin'))    
    else:
        return render_template('add_menu_item.html')


@app.route('/admin/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_menu_item(item_id):
    item = MenuItem.query.get(item_id)
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    if request.method == 'POST':
        
        item.name = request.form['name']
        item.description = request.form.get('description', '')
        item.price = request.form['price']

        db.session.commit()
        flash('Menu item updated successfully!', 'success')
        return redirect(url_for('admin'))
    else:
        return render_template('update_menu_item.html', item=item)


@app.route('/admin/menu/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_menu_item(item_id):
    item = MenuItem.query.get(item_id)
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin/orders')
@login_required
def view_admin_orders():
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    orders = Order.query.all()  
    return render_template('view_admin_orders.html', orders=orders)


@app.route('/user/order/<int:item_id>', methods=['POST'])
@login_required
def place_order(item_id):
    menu_item = MenuItem.query.get(item_id)
    existing_order = Order.query.filter_by(user_id=current_user.id, menu_item_id=item_id, status='Pending').first()

    if not existing_order:
        new_order = Order(status='Pending', user_id=current_user.id, menu_item_id=item_id)
        db.session.add(new_order)
        db.session.commit()
    
    return redirect(url_for('user'))


@app.route('/admin/order/complete/<int:order_id>', methods=['POST'])
@login_required
def complete_order(order_id):
    # if current_user.role != 'admin':
    #     return redirect(url_for('index'))

    order = Order.query.get(order_id)
    if order.status == 'Pending':
        order.status = 'Completed'
        db.session.commit()
    
    return redirect(url_for('view_admin_orders')) 


@app.route('/user/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get(order_id)
    order.status = 'Canceled'
    db.session.commit()

    return redirect(url_for('user'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
