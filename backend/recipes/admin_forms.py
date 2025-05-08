from django import forms

from recipes.models import Recipe


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk:
            ingredients_count = self.instance.recipe_ingredients.count()
        else:
            ingredients_count = 0

        if ingredients_count == 0:
            raise forms.ValidationError(
                'Нельзя сохранить рецепт без ингредиентов.'
            )
        return cleaned_data
