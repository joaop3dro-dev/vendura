from .models import CartItem


class CartItemRepository:
    @staticmethod
    def get_customer_cart_items_tuple(customer):
        return list(
            CartItem.objects.filter(
                cart__customer=customer, selected=CartItem.SelectedChoices.SELECTED
            ).values_list("item_id", "quantity")
        )

    @staticmethod
    def delete_customer_cart_items(customer):
        CartItem.objects.filter(
            cart__customer=customer, selected=CartItem.SelectedChoices.SELECTED
        ).delete()
