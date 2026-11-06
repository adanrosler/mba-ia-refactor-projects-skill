from models.category import Category
from utils.errors import NotFoundError
from validators.category_validator import validate_category_create, validate_category_update


class CategoryController:
    @staticmethod
    def _get_or_404(category_id):
        category = Category.find(category_id)
        if category is None:
            raise NotFoundError('Categoria não encontrada')
        return category

    def list_categories(self, page=None, per_page=None):
        task_counts = Category.task_counts()
        result = []
        for category in Category.list(page, per_page):
            data = category.to_dict()
            data['task_count'] = task_counts.get(category.id, 0)
            result.append(data)
        return result

    def create_category(self, payload):
        category = Category(**validate_category_create(payload))
        category.save('Erro ao criar categoria')
        return category.to_dict()

    def update_category(self, category_id, payload):
        category = self._get_or_404(category_id)
        for field, value in validate_category_update(payload).items():
            setattr(category, field, value)
        category.save('Erro ao atualizar')
        return category.to_dict()

    def delete_category(self, category_id):
        self._get_or_404(category_id).delete('Erro ao deletar')
        return {'message': 'Categoria deletada'}
