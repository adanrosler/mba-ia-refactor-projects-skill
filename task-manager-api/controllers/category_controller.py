from models.category import Category
from models.task import Task
from utils.errors import NotFoundError
from validators.category_validator import validate_category_create, validate_category_update


class CategoryController:
    def _get_or_404(self, category_id):
        category = Category.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category

    def list_categories(self, page=None, per_page=None):
        task_counts = Task.count_by(Task.category_id)
        return [
            {**category.to_dict(), 'task_count': task_counts.get(category.id, 0)}
            for category in Category.list_all(page, per_page)
        ]

    def create_category(self, data):
        fields = validate_category_create(data)
        category = Category(**fields)
        category.save('Erro ao criar categoria')
        return category.to_dict()

    def update_category(self, category_id, data):
        category = self._get_or_404(category_id)
        for field, value in validate_category_update(data).items():
            setattr(category, field, value)
        category.save('Erro ao atualizar')
        return category.to_dict()

    def delete_category(self, category_id):
        self._get_or_404(category_id).delete('Erro ao deletar')
        return {'message': 'Categoria deletada'}
