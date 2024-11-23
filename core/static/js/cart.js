$(document).ready(function() {
    // ویرایش تعداد محصول
    $('.update-quantity').on('change', function() {
        let cartItemId = $(this).data('id');
        let quantity = $(this).val();
        
        $.ajax({
            url: `/api/cart/${cartItemId}/`,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({ quantity: quantity }),
            success: function(response) {
                location.reload();
            }
        });
    });

    // حذف محصول از سبد خرید
    $('.delete-item').on('click', function(e) {
        e.preventDefault();
        let cartItemId = $(this).data('id');
        
        $.ajax({
            url: `/api/cart/${cartItemId}/`,
            method: 'DELETE',
            success: function(response) {
                // اینجا می‌توانید پیام موفقیت را نیز نمایش دهید
                location.reload();
            },
            error: function(response) {
                alert('خطا در حذف محصول');
            }
        });
    });
});
