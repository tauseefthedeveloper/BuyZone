import json
from django.contrib import admin, messages
from django.utils.html import format_html

from .models import (
    Product,
    Orders,
    CancelledPaidOrder,
    OrderUpdate,
    Contact,
    ProductVariant,
    Size
)

from .utils.refund import refund_payment


# ==================== CATEGORY FILTER ====================

class CategoryFilter(admin.SimpleListFilter):
    title = 'Category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        categories = (
            model_admin.model.objects
            .values_list('category', flat=True)
            .distinct()
            .order_by('category')
        )
        return [(c, c) for c in categories if c]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category=self.value())
        return queryset


# ==================== PRODUCT ADMIN ====================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'product_image',
        'product_name',
        'category',
        'subcategory',
        'price_display',
        'discount_display',
        'rating_stars'
    )

    fieldsets = (
        ('Basic Info', {'fields': ('product_name', 'category', 'subcategory')}),
        ('Pricing', {'fields': ('price', 'OldPrice', 'Discount', 'ShippingFee')}),
        ('Status', {'fields': ('Rating',)}),
        ('Description & Image', {'fields': ('desc', 'image')}),
    )

    list_filter = (CategoryFilter, 'Rating')
    search_fields = ('product_name', 'category', 'subcategory', 'id')
    list_display_links = ('id',)

    def price_display(self, obj):
        return format_html(
            '<b style="color:#198754;">₹{}</b><br><del style="color:#dc3545;">₹{}</del>',
            obj.price, obj.OldPrice
        )
    price_display.short_description = "Price"

    def discount_display(self, obj):
        return format_html('<span style="color:#dc3545;">{}% OFF</span>', obj.Discount)
    discount_display.short_description = "Discount"

    def rating_stars(self, obj):
        return "⭐" * obj.Rating if obj.Rating else "-"
    rating_stars.short_description = "Rating"

    @admin.display(description="Image")
    def product_image(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html(
                '<img src="{}" loading="lazy" width="50" style="border-radius:8px;"/>',
                obj.image.url
            )
        return "—"


# ==================== SIZE ADMIN ====================

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# ==================== PRODUCT VARIANT ====================

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product_info", "size", "stock")
    search_fields = ("product__product_name", "product__id", "size__name")

    def product_info(self, obj):
        return f"ID:{obj.product.id} | {obj.product.product_name}"
    product_info.short_description = "Product"


# ==================== ORDER UPDATE ====================

@admin.register(OrderUpdate)
class OrderUpdateAdmin(admin.ModelAdmin):

    list_display = ('order_oid', 'short_update', 'delivered', 'update_date')
    list_editable = ('delivered',)
    list_filter = ('delivered', 'update_date')
    readonly_fields = ('update_date',)
    ordering = ('-update_date',)
    search_fields = ('order__oid',)

    def has_add_permission(self, request):
        return False

    def short_update(self, obj):
        return obj.update_desc[:60] + "..." if len(obj.update_desc) > 60 else obj.update_desc

    def order_oid(self, obj):
        return obj.order.oid
    order_oid.short_description = "Order ID"


# ==================== ORDERS ADMIN ====================

@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):

    list_display = ('oid', 'amount', 'paymentstatus', 'BookDate', 'amountpaid')
    list_editable = ('paymentstatus',)
    list_display_links = ('oid',)
    list_filter = ('paymentstatus', 'BookDate', 'email')
    search_fields = ('oid', 'email', 'name')
    date_hierarchy = 'BookDate'

    exclude = ('items_json',)

    readonly_fields = (
        'items_json_formatted',
        'amount',
        'amountpaid',
        'BookDate',
        'is_returned',
        'delivered_at',
        'is_refunded',
        'payment_id',
        'refund_id',
    )

    fieldsets = (
        ('Customer Info', {'fields': ('name', 'email', 'phone')}),
        ('Address', {'fields': ('address1', 'address2', 'city', 'state', 'zip_code')}),
        ('Order Items', {'fields': ('items_json_formatted',)}),
        ('Payment', {'fields': ('amount', 'amountpaid', 'paymentstatus', 'BookDate')}),
        ('Delivery', {'fields': ('assigned_to', 'is_returned', 'delivered_at')}),
    )

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        assigned_changed = False
        if change:
            old = Orders.objects.get(pk=obj.pk)
            assigned_changed = old.assigned_to != obj.assigned_to

        super().save_model(request, obj, form, change)

        if assigned_changed and obj.assigned_to:
            OrderUpdate.objects.create(
                order=obj,
                update_desc="Order assigned to delivery partner",
                delivered=False
            )

    def items_json_formatted(self, obj):
        if not obj.items_json:
            return "-"

        data = json.loads(obj.items_json) if isinstance(obj.items_json, str) else obj.items_json
        html = ""

        for pid, values in data.items():
            qty, name, price, mrp, discount, size = values
            product_id = int(str(pid).replace("pr", "")) if str(pid).startswith("pr") else int(pid)
            product = Product.objects.filter(id=product_id).first()

            image = (
                f'<img src="{product.image.url}" loading="lazy" width="120" style="border-radius:8px;">'
                if product and product.image else "—"
            )

            html += f"""
            <div style="display:flex;gap:16px;margin-bottom:12px;padding:12px;border:1px solid #e0e0e0;border-radius:10px;">
              <div>
                <b>{name}</b><br>
                <span style="color:#0d6efd;">Qty:</span> {qty}<br>
                <span style="color:#198754;">₹{price}</span>
                <del style="color:#dc3545;">₹{mrp}</del><br>
                Discount: {discount}<br>
                Size: {size}
              </div>
              <div>{image}</div>
            </div>
            """

        return format_html(html)

    items_json_formatted.short_description = "Ordered Items"


# ==================== CANCELLED / REFUND ====================

@admin.register(CancelledPaidOrder)
class CancelledPaidOrderAdmin(admin.ModelAdmin):

    actions = ['refund_selected_orders']

    list_display = (
        'oid',
        'paymentstatus',
        'BookDate',
        'amountpaid',
        'refund_status',
    )

    date_hierarchy = 'BookDate'
    list_filter = ('paymentstatus', 'BookDate', 'email')
    search_fields = ('oid', 'email', 'name')

    exclude = ('items_json',)

    readonly_fields = (
        'items_json_formatted',
        'amount',
        'amountpaid',
        'BookDate',
        'payment_id',
        'refund_id',
        'refund_status',
    )

    fieldsets = (
        ('Customer Info', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address1', 'address2', 'city', 'state', 'zip_code')
        }),
        ('Order Items', {
            'fields': ('items_json_formatted',),
        }),
        ('Payment', {
            'fields': ('amount', 'amountpaid', 'paymentstatus', 'BookDate')
        }),
        ('Refund', {
            'fields': ('refund_status', 'payment_id', 'refund_id')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            paymentstatus__in=['Cancelled', 'Return Completed'],
            amountpaid__gt=0
        )

    # ✅ MISSING METHOD (THIS FIXES YOUR ERROR)
    def items_json_formatted(self, obj):
        if not obj.items_json:
            return "-"

        data = json.loads(obj.items_json) if isinstance(obj.items_json, str) else obj.items_json
        html = ""

        for pid, values in data.items():
            qty, name, price, mrp, discount, size = values

            product_id = int(str(pid).replace("pr", "")) if str(pid).startswith("pr") else int(pid)
            product = Product.objects.filter(id=product_id).first()

            image = (
                f'<img src="{product.image.url}" loading="lazy" width="120" style="border-radius:8px;">'
                if product and product.image else "—"
            )

            html += f"""
            <div style="
                display:flex;
                gap:16px;
                margin-bottom:12px;
                padding:12px;
                border:1px solid #e0e0e0;
                border-radius:10px;
                background:#fdfdfd;
                align-items:center;
            ">
              <div>
                <b>{name}</b><br>
                <span style="color:#0d6efd;">Qty:</span> {qty}<br>
                <span style="color:#198754;">₹{price}</span>
                <del style="color:#dc3545;">₹{mrp}</del><br>
                Discount: {discount}<br>
                Size: {size}
              </div>
              <div>{image}</div>
            </div>
            """

        return format_html(html)

    items_json_formatted.short_description = "Ordered Items"

    def refund_status(self, obj):
        return "Refunded ✅" if obj.is_refunded else "Pending ❌"
    refund_status.short_description = "Refund Status"

    def refund_selected_orders(self, request, queryset):
        for order in queryset:

            if order.is_refunded:
                messages.warning(request, f"Order {order.oid} already refunded")
                continue

            if not order.payment_id:
                messages.warning(
                    request,
                    f"COD Order {order.oid}: Refund handled manually"
                )
                continue

            try:
                res = refund_payment(order.payment_id, order.amountpaid)
                order.refund_id = res["id"]
                order.is_refunded = True
                order.save()

                OrderUpdate.objects.create(
                    order=order,
                    update_desc=f"Refund completed. Refund ID: {res['id']}",
                    delivered=False
                )

                messages.success(request, f"Refund successful for Order {order.oid}")

            except Exception as e:
                messages.error(
                    request,
                    f"Refund failed for Order {order.oid}: {str(e)}"
                )

    refund_selected_orders.short_description = "Refund Selected Orders"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ==================== CONTACT ADMIN ====================

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):

    list_display = ('name', 'email_link', 'phone_display')
    search_fields = ('name', 'email', 'phoneNo')

    def has_add_permission(self, request):
        return False

    def email_link(self, obj):
        return format_html('<a href="mailto:{}">{}</a>', obj.email, obj.email)
    email_link.short_description = "Email"

    def phone_display(self, obj):
        return obj.phoneNo
    phone_display.short_description = "Phone"
# ==================== REFUND LOGIC IN ORDER ADMIN ====================