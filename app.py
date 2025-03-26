from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory01.db'
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    asin = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    fba_available_stock = db.Column(db.Integer, nullable=False, default=0)
    total_sales_last_30_days = db.Column(db.Integer, nullable=False, default=0)
    period_days = db.Column(db.Integer, nullable=False, default=30)
    seasonality_factor = db.Column(db.Float, nullable=False, default=1.0)
    adj_velocity = db.Column(db.Float, nullable=False, default=0.0)
    fba_days_remaining = db.Column(db.Integer, nullable=False, default=0)
    forecast = db.Column(db.Integer, nullable=False, default=0) # ! THIS IS GOOD

    def calculate_adjusted_velocity(self):
        if self.period_days > 0:
            return (self.total_sales_last_30_days / self.period_days) * self.seasonality_factor
        return 0.0

    def calculate_fba_days_remaining(self):
        if self.adj_velocity > 0:
            return self.fba_available_stock / self.adj_velocity
        return 0
    
    def calculate_forecast(self): # ! THIS ONE TOO!
        if self.fba_days_remaining > 0:
            return self.fba_days_remaining + 45
        return 0
    
# 🔸 This will auto-create the DB when the app starts (useful for Render)
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    items = Item.query.all()
    return render_template('index.html', items=items)

@app.route('/add', methods=['POST'])
def add_item():
    name = request.form.get('name')
    asin = request.form.get('asin')
    category = request.form.get('category')
    fba_available_stock = request.form.get('fba_available_stock', type=int)
    total_sales_last_30_days = request.form.get('total_sales_last_30_days', type=int)
    period_days = request.form.get('period_days', type=int)
    seasonality_factor = request.form.get('seasonality_factor', type=float)
    
    if name and asin and category:
        new_item = Item(
            name=name,
            asin=asin,
            category=category,
            fba_available_stock=fba_available_stock,
            total_sales_last_30_days=total_sales_last_30_days,
            period_days=period_days,
            seasonality_factor=seasonality_factor
        )
        
        new_item.adj_velocity = new_item.calculate_adjusted_velocity()
        new_item.fba_days_remaining = new_item.calculate_fba_days_remaining()
        new_item.forecast = new_item.calculate_forecast() #! THIS IS GOOD TOO!
        
        db.session.add(new_item)
        db.session.commit()
    
    return redirect(url_for('home'))

@app.route('/remove/<int:item_id>')
def remove_product(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(host='0.0.0.0', port=5015, debug=True)