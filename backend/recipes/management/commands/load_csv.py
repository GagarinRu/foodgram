from csv import reader

from django.core.management import BaseCommand

from recipes.models import Ingredient, Tag


TABLES_DICT = {
    Ingredient: 'ingredients.csv',
    Tag: 'tags.csv',
}


class Command(BaseCommand):
    help = 'Загрузка данных из csv файлов'

    def handle(self, *args, **options):
        for model_name, file_name in TABLES_DICT.items():
            try:
                with open(
                    f'./data/{file_name}',
                    encoding='utf-8'
                ) as csv_file:
                    data_list = []
                    data = reader(csv_file)
                    for row_one, row_two in data:
                        if 'tags.csv' in file_name:
                            data_list.append(
                                model_name(
                                    name=row_one,
                                    slug=row_two
                                )
                            )
                        elif 'ingredients.csv' in file_name:
                            data_list.append(
                                model_name(
                                    name=row_one,
                                    measurement_unit=row_two
                                )
                            )
                    model_name.objects.bulk_create(
                        data_list,
                        ignore_conflicts=True
                    )
            except Exception as error:
                self.stdout.write(self.style.ERROR(f'{error}'))
        self.stdout.write(self.style.SUCCESS('Загрузка данных завершена'))
