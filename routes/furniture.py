from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db
from models.furniture import FurnitureCategory, FurnitureItem
from routes.auth import login_required, role_required
from services.audit_service import log_audit

furniture_bp = Blueprint('furniture', __name__, url_prefix='/furniture')

@furniture_bp.route('/items')
@login_required
def items():
    categories = FurnitureCategory.query.filter_by(is_active=True).order_by(FurnitureCategory.name.asc()).all()
    selected_cat = request.args.get('category_id', type=int)
    
    query = FurnitureItem.query.filter_by(is_active=True)
    if selected_cat:
        query = query.filter_by(category_id=selected_cat)
    
    items_list = query.order_by(FurnitureItem.name.asc()).all()
    return render_template('furniture/items.html', items=items_list, categories=categories, selected_cat=selected_cat)

@furniture_bp.route('/items/add', methods=['POST'])
@login_required
@role_required(['OWNER'])
def add_item():
    name = request.form.get('name', '').strip()
    category_id = request.form.get('category_id', type=int)
    description = request.form.get('description', '').strip()

    if not name or not category_id:
        flash('Item name and category are required.', 'danger')
        return redirect(url_for('furniture.items'))

    item = FurnitureItem(name=name, category_id=category_id, description=description, is_active=True)
    db.session.add(item)
    db.session.commit()

    log_audit('ADD_FURNITURE_ITEM', table_name='furniture_items', record_id=item.id, details=f"Added item: {name}")
    flash(f'Furniture item "{name}" added successfully.', 'success')
    return redirect(url_for('furniture.items'))

@furniture_bp.route('/items/edit/<int:item_id>', methods=['POST'])
@login_required
@role_required(['OWNER'])
def edit_item(item_id):
    item = FurnitureItem.query.get_or_404(item_id)
    item.name = request.form.get('name', item.name).strip()
    item.category_id = request.form.get('category_id', item.category_id, type=int)
    item.description = request.form.get('description', '').strip()

    db.session.commit()
    log_audit('EDIT_FURNITURE_ITEM', table_name='furniture_items', record_id=item.id, details=f"Updated item: {item.name}")
    flash(f'Furniture item "{item.name}" updated.', 'success')
    return redirect(url_for('furniture.items'))

@furniture_bp.route('/items/delete/<int:item_id>', methods=['POST'])
@login_required
@role_required(['OWNER'])
def delete_item(item_id):
    item = FurnitureItem.query.get_or_404(item_id)
    item.is_active = False
    db.session.commit()
    log_audit('DELETE_FURNITURE_ITEM', table_name='furniture_items', record_id=item.id, details=f"Deactivated item: {item.name}")
    flash(f'Furniture item "{item.name}" deactivated.', 'info')
    return redirect(url_for('furniture.items'))

@furniture_bp.route('/categories')
@login_required
def categories():
    cats = FurnitureCategory.query.filter_by(is_active=True).order_by(FurnitureCategory.name.asc()).all()
    return render_template('furniture/categories.html', categories=cats)

@furniture_bp.route('/categories/add', methods=['POST'])
@login_required
@role_required(['OWNER'])
def add_category():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('furniture.categories'))

    existing = FurnitureCategory.query.filter_by(name=name).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.description = description
            db.session.commit()
            flash(f'Reactivated category "{name}".', 'success')
            return redirect(url_for('furniture.categories'))
        flash(f'Category "{name}" already exists.', 'warning')
        return redirect(url_for('furniture.categories'))

    cat = FurnitureCategory(name=name, description=description, is_active=True)
    db.session.add(cat)
    db.session.commit()

    log_audit('ADD_FURNITURE_CATEGORY', table_name='furniture_categories', record_id=cat.id, details=f"Added category: {name}")
    flash(f'Furniture category "{name}" added.', 'success')
    return redirect(url_for('furniture.categories'))

@furniture_bp.route('/categories/edit/<int:cat_id>', methods=['POST'])
@login_required
@role_required(['OWNER'])
def edit_category(cat_id):
    cat = FurnitureCategory.query.get_or_404(cat_id)
    cat.name = request.form.get('name', cat.name).strip()
    cat.description = request.form.get('description', '').strip()
    db.session.commit()

    log_audit('EDIT_FURNITURE_CATEGORY', table_name='furniture_categories', record_id=cat.id, details=f"Updated category: {cat.name}")
    flash(f'Category "{cat.name}" updated.', 'success')
    return redirect(url_for('furniture.categories'))

@furniture_bp.route('/categories/delete/<int:cat_id>', methods=['POST'])
@login_required
@role_required(['OWNER'])
def delete_category(cat_id):
    cat = FurnitureCategory.query.get_or_404(cat_id)
    cat.is_active = False
    db.session.commit()

    log_audit('DELETE_FURNITURE_CATEGORY', table_name='furniture_categories', record_id=cat.id, details=f"Deactivated category: {cat.name}")
    flash(f'Category "{cat.name}" deactivated.', 'info')
    return redirect(url_for('furniture.categories'))

@furniture_bp.route('/api/items')
@login_required
def api_items():
    cat_id = request.args.get('category_id', type=int)
    query = FurnitureItem.query.filter_by(is_active=True)
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    items_data = [item.to_dict() for item in query.order_by(FurnitureItem.name.asc()).all()]
    return jsonify(items_data)
