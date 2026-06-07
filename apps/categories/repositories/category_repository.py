from apps.categories.models import Category


class CategoryRepository:
    def get_all(self, level=None, search=None):
        qs = Category.objects.all()
        if level is not None:
            qs = qs.filter(level=level)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

    def get_by_id(self, pk):
        return Category.objects.filter(pk=pk).first()

    def create(self, **kwargs):
        return Category.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance
