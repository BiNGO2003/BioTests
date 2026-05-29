#!/usr/bin/env python
"""
╔══════════════════════════════════════════════════════════╗
║   ExamPrep — Импорт тестов из Word в Django              ║
║   Использование:                                          ║
║     python import_tests.py biology tests.docx            ║
║     python import_tests.py chemistry chemistry.docx      ║
╚══════════════════════════════════════════════════════════╝

ФОРМАТ WORD ФАЙЛА:
──────────────────
  Название теста        ← первая строка (заголовок темы)

  1. Текст вопроса
  А) вариант 1
  Б) вариант 2
  В) вариант 3
  Г) вариант 4
  Д) вариант 5        ← опционально
  Ответ: А            ← или просто "А) 1,3"

Поддерживаемые буквы: А Б В Г Д  (и A B C D E латинские)
"""

import os
import sys
import re
import django

# ── Настройка Django ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Test, Question
from docx import Document as DocxDocument

# ── Константы ─────────────────────────────────────────────────────────────────
SUBJECT_MAP = {
    'biology':   'biology',
    'bio':       'biology',
    'биология':  'biology',
    'chemistry': 'chemistry',
    'chem':      'chemistry',
    'химия':     'chemistry',
    'math':      'math',
    'математика':'math',
    'history':   'history',
    'история':   'history',
    'russian':   'russian',
    'русский':   'russian',
}

DIFFICULTY_MAP = {
    'easy':    'easy',
    'лёгкий':  'easy',
    'medium':  'medium',
    'средний': 'medium',
    'hard':    'hard',
    'сложный': 'hard',
}

# Буквы вариантов (рус и лат)
OPTION_LETTERS = {
    'А': 0, 'A': 0,
    'Б': 1, 'B': 1,
    'В': 2, 'C': 2,
    'Г': 3, 'D': 3,
    'Д': 4, 'E': 4,
}

# Паттерны для распознавания строк
RE_QUESTION  = re.compile(r'^(\d+)[.)\s]\s*(.+)', re.S)
RE_OPTION    = re.compile(r'^([АБВГДABCDEабвгд])[.)]\s*(.+)', re.S)
RE_ANSWER    = re.compile(r'^(?:ответ|answer)[:\s]*([АБВГДABCDEабвгд])', re.I)
RE_INLINE_ANS= re.compile(r'\b([АБВГДABCDEабвгд])\)\s*[\d,\s]+$')


# ══════════════════════════════════════════════════════════════════════════════
#  ПАРСЕР
# ══════════════════════════════════════════════════════════════════════════════
def parse_docx(filepath):
    """Читает Word файл и возвращает список блоков вопросов."""
    doc = DocxDocument(filepath)
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return lines


def extract_tests(lines):
    """
    Разбивает текст на тесты и вопросы.
    Возвращает список: [{'title': ..., 'questions': [...]}]
    """
    tests = []
    current_test  = None
    current_q     = None
    current_opts  = {}   # letter_index -> text
    current_ans   = None

    def save_question():
        nonlocal current_q, current_opts, current_ans
        if current_q and current_test is not None and len(current_opts) >= 2:
            # Нормализуем варианты в список [A, B, C, D]
            opts_list = []
            for i in range(4):
                opts_list.append(current_opts.get(i, ''))

            # Определяем правильный ответ
            correct = current_ans if current_ans is not None else 0

            # Убираем пустые последние варианты
            while opts_list and not opts_list[-1]:
                opts_list.pop()

            # Минимум 2 варианта
            if len([o for o in opts_list if o]) >= 2:
                # Дополняем до 4 если нужно
                while len(opts_list) < 4:
                    opts_list.append(f'Вариант {len(opts_list)+1}')

                current_test['questions'].append({
                    'text':    current_q,
                    'options': opts_list[:4],
                    'correct': correct,
                })
        current_q    = None
        current_opts = {}
        current_ans  = None

    for line in lines:
        # Новый тест — строка без номера, похожа на заголовок
        m_q = RE_QUESTION.match(line)
        m_o = RE_OPTION.match(line)
        m_a = RE_ANSWER.match(line)

        if m_a:
            # Строка "Ответ: А"
            letter = m_a.group(1).upper()
            current_ans = OPTION_LETTERS.get(letter, 0)

        elif m_o:
            # Строка варианта ответа "А) текст"
            letter = m_o.group(1).upper()
            text   = m_o.group(2).strip()
            idx    = OPTION_LETTERS.get(letter, len(current_opts))

            # Если это строка с ответами в конце вопроса типа "А) 1,3  Б) 2,4"
            # обрабатываем как одну строку с несколькими вариантами
            if current_test is not None:
                current_opts[idx] = text
                # Проверяем есть ли ответ в самой строке варианта
                # (когда правильный ответ — первый вариант после вопроса)

        elif m_q:
            # Новый вопрос
            save_question()
            if current_test is not None:
                current_q = m_q.group(2).strip()
                current_opts = {}
                current_ans  = None

        else:
            # Строка без явного паттерна
            if current_test is None:
                # Это заголовок нового теста
                title = line.strip()
                if len(title) > 2:   # игнорируем пустышки
                    current_test = {'title': title, 'questions': []}
                    tests.append(current_test)
            elif current_q and not current_opts:
                # Продолжение текста вопроса
                current_q += ' ' + line
            elif current_q and current_opts:
                # Возможно продолжение последнего варианта
                last_idx = max(current_opts.keys()) if current_opts else None
                if last_idx is not None:
                    current_opts[last_idx] += ' ' + line

    save_question()
    return tests


def detect_answer_from_options(question_text, options):
    """
    Если ответ не указан явно, пытаемся найти его в тексте вопроса
    (формат "А) 1,3  Б) 2,5  В) 4,6  Г) 3,5" в конце вопроса).
    В таком случае варианты А/Б/В/Г и есть ответы — берём первый = 0.
    """
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  ЗАГРУЗКА В DJANGO
# ══════════════════════════════════════════════════════════════════════════════
def import_to_django(tests_data, subject, difficulty='medium', time_limit=15):
    total_tests = 0
    total_questions = 0
    errors = []

    for test_data in tests_data:
        title     = test_data['title']
        questions = test_data['questions']

        if not questions:
            print(f'  ⚠️  Тест "{title}" — вопросов не найдено, пропускаем')
            continue

        # Создаём или обновляем тест
        test, created = Test.objects.get_or_create(
            name=title,
            subject=subject,
            defaults={
                'difficulty':  difficulty,
                'time_limit':  time_limit,
                'description': f'Импортировано из Word',
            }
        )
        action = 'создан' if created else 'обновлён'
        print(f'\n  📋 Тест "{title}" — {action}')

        added = 0
        for q in questions:
            opts = q['options']
            # Убеждаемся что есть 4 варианта
            while len(opts) < 4:
                opts.append(f'—')

            try:
                Question.objects.create(
                    test        = test,
                    text        = q['text'],
                    option_a    = opts[0],
                    option_b    = opts[1],
                    option_c    = opts[2],
                    option_d    = opts[3],
                    correct     = q['correct'],
                    explanation = '',
                )
                added += 1
            except Exception as e:
                errors.append(f'Вопрос "{q["text"][:50]}": {e}')

        print(f'     ✅ Добавлено {added} вопросов')
        total_tests += 1
        total_questions += added

    return total_tests, total_questions, errors


# ══════════════════════════════════════════════════════════════════════════════
#  ГЛАВНАЯ ФУНКЦИЯ
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print('\n' + '═'*55)
    print('  ExamPrep — Импорт тестов из Word')
    print('═'*55)

    # Аргументы командной строки
    if len(sys.argv) < 3:
        print('\nИспользование:')
        print('  python import_tests.py <предмет> <файл.docx> [сложность] [время]')
        print('\nПредметы:')
        print('  biology / chemistry / math / history / russian')
        print('\nПример:')
        print('  python import_tests.py biology birds.docx medium 15')
        print('  python import_tests.py chemistry organic.docx hard 20')
        sys.exit(1)

    subject_arg    = sys.argv[1].lower()
    filepath       = sys.argv[2]
    difficulty_arg = sys.argv[3].lower() if len(sys.argv) > 3 else 'medium'
    time_limit     = int(sys.argv[4]) if len(sys.argv) > 4 else 15

    # Валидация предмета
    subject = SUBJECT_MAP.get(subject_arg)
    if not subject:
        print(f'\n❌ Неизвестный предмет: {subject_arg}')
        print(f'   Доступные: {", ".join(SUBJECT_MAP.keys())}')
        sys.exit(1)

    # Валидация сложности
    difficulty = DIFFICULTY_MAP.get(difficulty_arg, 'medium')

    # Проверка файла
    if not os.path.exists(filepath):
        print(f'\n❌ Файл не найден: {filepath}')
        sys.exit(1)

    print(f'\n📂 Файл:     {filepath}')
    print(f'📚 Предмет:  {subject}')
    print(f'🎯 Сложность: {difficulty}')
    print(f'⏱  Время:    {time_limit} мин')
    print('\n' + '─'*55)

    # Парсинг
    print('\n🔍 Читаю файл...')
    lines = parse_docx(filepath)
    print(f'   Строк найдено: {len(lines)}')

    print('\n🔍 Разбираю вопросы...')
    tests_data = extract_tests(lines)

    if not tests_data:
        print('\n❌ Тестов не найдено. Проверь формат файла.')
        print('   Первая строка должна быть названием темы (без номера).')
        sys.exit(1)

    print(f'   Тестов найдено: {len(tests_data)}')
    total_q = sum(len(t['questions']) for t in tests_data)
    print(f'   Вопросов найдено: {total_q}')

    # Показываем предпросмотр
    print('\n' + '─'*55)
    print('📋 ПРЕДПРОСМОТР:')
    for t in tests_data:
        print(f'\n  [{t["title"]}] — {len(t["questions"])} вопр.')
        for i, q in enumerate(t['questions'][:2]):
            print(f'    {i+1}. {q["text"][:70]}')
            for j, opt in enumerate(q['options']):
                marker = '✓' if j == q['correct'] else ' '
                print(f'       {marker} {["А","Б","В","Г"][j]}) {opt[:50]}')
        if len(t['questions']) > 2:
            print(f'    ... и ещё {len(t["questions"])-2} вопросов')

    # Подтверждение
    print('\n' + '─'*55)
    ans = input('\n▶ Загрузить в базу данных? (да/нет): ').strip().lower()
    if ans not in ('да', 'yes', 'y', 'д'):
        print('Отменено.')
        sys.exit(0)

    # Загрузка
    print('\n🚀 Загружаю в Django...')
    total_tests, total_q, errors = import_to_django(
        tests_data, subject, difficulty, time_limit
    )

    # Итог
    print('\n' + '═'*55)
    print(f'✅ ГОТОВО!')
    print(f'   Тестов загружено:   {total_tests}')
    print(f'   Вопросов загружено: {total_q}')
    if errors:
        print(f'\n⚠️  Ошибки ({len(errors)}):')
        for e in errors:
            print(f'   - {e}')
    print('═'*55 + '\n')


if __name__ == '__main__':
    main()
