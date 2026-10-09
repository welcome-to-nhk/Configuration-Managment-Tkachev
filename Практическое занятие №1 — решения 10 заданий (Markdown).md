# Практическое занятие №1. Введение, основы работы в командной строке

**Дисциплина:** Конфигурационное управление, РТУ МИРЭА, П.Н. Советов  
**Источник заданий:** [true-grue/kisscm — pract1.md](https://github.com/true-grue/kisscm/blob/main/pract/pract1.md)

---

## Задание 1

**Задание**

Вывести отсортированный в алфавитном порядке список имен пользователей в файле passwd (вам понадобится grep).

**Код**

```bash
grep -Eo '^[^:]+' /etc/passwd | sort
```

**Вывод**

```
_apt
_chrony
backup
bin
daemon
dhcpcd
games
irc
list
lp
mail
man
messagebus
news
nobody
proxy
root
sshd
sync
sys
systemd-network
systemd-resolve
user
uucp
www-data
```

---

## Задание 2

**Задание**

Вывести данные /etc/protocols в отформатированном и отсортированном порядке для 5 наибольших портов, как показано в примере ниже:

```
[root@localhost etc]# cat /etc/protocols ...
142 rohc
141 wesp
140 shim6
139 hip
138 manet
```

**Код**

```bash
awk '!/^#/ && NF >= 2 && $2 ~ /^[0-9]+$/ { print $2, $1 }' /etc/protocols | sort -k1,1nr | head -n 5
```

**Вывод**

```
262 mptcp
143 ethernet
142 rohc
141 wesp
140 shim6
```

---

## Задание 3

**Задание**

Написать программу banner средствами bash для вывода текстов, как в следующем примере (размер баннера должен меняться!):

```
[root@localhost ~]# ./banner "Hello from RTU MIREA!"
+-----------------------+
| Hello from RTU MIREA! |
+-----------------------+
```

Перед отправкой решения проверьте его в ShellCheck на предупреждения.

**Код**

```bash
cat > banner <<'EOF'
#!/bin/bash
# banner: вывод текста в рамке (размер зависит от текста)
if [ $# -ne 1 ]; then
    echo "Использование: $0 <текст>" >&2
    exit 1
fi

text=$1
width=$(( ${#text} + 2 ))
line=$(printf '%*s' "$width" '' | tr ' ' '-')
printf '+%s+\n|%s|\n+%s+\n' "$line" " $text " "$line"
EOF
chmod +x banner

shellcheck banner
./banner "Hello from RTU MIREA!"
./banner "Hi"
```

**Вывод**

```
+-----------------------+
| Hello from RTU MIREA! |
+-----------------------+
+----+
| Hi |
+----+
```

---

## Задание 4

**Задание**

Написать программу для вывода всех идентификаторов (по правилам C/C++ или Java) в файле (без повторений).

Пример для hello.c:

```
h hello include int main n printf return stdio void world
```

**Код**

```bash
cat > identifiers <<'EOF'
#!/bin/bash
# identifiers: вывод всех идентификаторов (C/C++/Java) в файле без повторений
if [ $# -ne 1 ]; then
    echo "Использование: $0 <файл>" >&2
    exit 1
fi

LC_ALL=C grep -owE '[A-Za-z_][A-Za-z0-9_]*' "$1" | LC_ALL=C sort -u | tr '\n' ' '
echo
EOF
chmod +x identifiers

cat > hello.c <<'CEOF'
#include <stdio.h>

int main(void) {
    printf("hello world\n");
    return 0;
}
CEOF
./identifiers hello.c
printf 'int valid_1; int _ok; int 123abc;\n' > mixed.txt
./identifiers mixed.txt
```

**Вывод**

```
h hello include int main n printf return stdio void world 
_ok int valid_1 
```

---

## Задание 5

**Задание**

Написать программу для регистрации пользовательской команды (правильные права доступа и копирование в /usr/local/bin).

Например, пусть программа называется reg:

```
./reg banner
```

В результате для banner задаются правильные права доступа и сам banner копируется в /usr/local/bin.

**Код**

```bash
cat > reg <<'EOF'
#!/bin/bash
# reg: регистрация пользовательской команды (права 755 + копирование в /usr/local/bin)
if [ $# -ne 1 ]; then
    echo "Использование: $0 <скрипт>" >&2
    exit 1
fi
if [ ! -f "$1" ]; then
    echo "$1: файл не найден" >&2
    exit 1
fi

chmod 755 "$1"
if [ "$(id -u)" -eq 0 ]; then
    install -m 755 "$1" /usr/local/bin/
else
    sudo install -m 755 "$1" /usr/local/bin/
fi
echo "Команда $1 зарегистрирована в /usr/local/bin"
EOF
chmod +x reg

./reg banner
ls -l /usr/local/bin/banner
banner "Registered!"
```

**Вывод**

```
Команда banner зарегистрирована в /usr/local/bin
-rwxr-xr-x 1 root root 338 Oct  8 21:30 /usr/local/bin/banner
+-------------+
| Registered! |
+-------------+
```

---

## Задание 6

**Задание**

Написать программу для проверки наличия комментария в первой строке файлов с расширением c, js и py.

**Код**

```bash
cat > check_comment <<'EOF'
#!/bin/bash
# check_comment: проверка наличия комментария в первой строке файлов .c, .js, .py
if [ $# -eq 0 ]; then
    echo "Использование: $0 <файл> [файл ...]" >&2
    exit 1
fi

# Комментарий ищется в любом месте первой строки. Разбор выполняется лексером
# Pygments (зависимость; установка: pip install pygments или
# sudo apt install python3-pygments): маркеры внутри строк, символьных литералов
# и регулярных выражений не считаются комментариями. Для C директивы #include
# (Comment.Preproc) комментариями не считаются.
python3 - "$@" <<'PYEOF'
import sys

from pygments import lex
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

for path in sys.argv[1:]:
    try:
        lexer = get_lexer_for_filename(path)
    except ClassNotFound:
        print(f"{path}: неподдерживаемое расширение (нужны .c, .js, .py)",
              file=sys.stderr)
        continue
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            first = f.readline()
    except OSError:
        print(f"{path}: файл не найден", file=sys.stderr)
        continue
    has_comment = False
    for token_type, _ in lex(first, lexer):
        token = str(token_type)
        if token.startswith("Token.Comment") and \
                not token.startswith("Token.Comment.Preproc"):
            has_comment = True
            break
    print(f"{path}: комментарий есть" if has_comment
          else f"{path}: комментария нет")
PYEOF
EOF
chmod +x check_comment

mkdir -p demo
printf '// Учебная программа\nint x = 1;\n' > demo/hello.c
printf 'int x; // комментарий после кода\n' > demo/after_code.c
printf '#include <stdio.h>\n' > demo/inc.c
printf "char c = '\"'; // \"комментарий\"\n" > demo/quote.c
printf 'const url = `https://example.org`;\n' > demo/url.js
printf 'const s = `${1 /* комментарий */}`;\n' > demo/interp.js
printf 'const slash = /\\//;\n' > demo/regex.js
printf 'console.log("hi");\n' > demo/script.js
printf '# Точка входа\nprint(1)\n' > demo/main.py
printf 'print("#")\n' > demo/calc.py
./check_comment demo/hello.c demo/after_code.c demo/inc.c demo/quote.c demo/url.js demo/interp.js demo/regex.js demo/script.js demo/main.py demo/calc.py
```

**Вывод**

```
demo/hello.c: комментарий есть
demo/after_code.c: комментарий есть
demo/inc.c: комментария нет
demo/quote.c: комментарий есть
demo/url.js: комментария нет
demo/interp.js: комментарий есть
demo/regex.js: комментария нет
demo/script.js: комментария нет
demo/main.py: комментарий есть
demo/calc.py: комментария нет
```

---

## Задание 7

**Задание**

Написать программу для нахождения файлов-дубликатов (имеющих 1 или более копий содержимого) по заданному пути (и подкаталогам).

**Код**

```bash
cat > dupfind <<'EOF'
#!/bin/bash
# dupfind: поиск файлов-дубликатов по содержимому (рекурсивно, по заданному пути)
if [ $# -ne 1 ]; then
    echo "Использование: $0 <каталог>" >&2
    exit 1
fi

find "$1" -type f -print0 | xargs -0 md5sum | sort | uniq --all-repeated=separate -w32
EOF
chmod +x dupfind

mkdir -p demo/dup/sub
printf 'RTU MIREA\n' > demo/dup/a.txt
printf 'RTU MIREA\n' > demo/dup/b.txt
printf 'RTU MIREA\n' > demo/dup/sub/c.txt
printf 'unique content\n' > demo/dup/unique.txt
./dupfind demo/dup
```

**Вывод**

```
c01f0c4660a17154d7f77b6e83b17fc8  demo/dup/a.txt
c01f0c4660a17154d7f77b6e83b17fc8  demo/dup/b.txt
c01f0c4660a17154d7f77b6e83b17fc8  demo/dup/sub/c.txt
```

---

## Задание 8

**Задание**

Написать программу, которая находит все файлы в данном каталоге с расширением, указанным в качестве аргумента и архивирует все эти файлы в архив tar.

**Код**

```bash
cat > tarext <<'EOF'
#!/bin/bash
# tarext: архивирование всех файлов с заданным расширением в tar-архив
if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    echo "Использование: $0 <расширение> <каталог> [архив.tar]" >&2
    exit 1
fi

ext=$1
dir=$2
archive=${3:-archive.tar}

find "$dir" -maxdepth 1 -type f -name "*.$ext" -print0 |
    tar -cf "$archive" --null -T -
echo "Создан архив: $archive"
echo "Содержимое архива:"
tar -tf "$archive"
EOF
chmod +x tarext

mkdir -p demo/tar
printf 'a\n' > demo/tar/a.c
printf 'b\n' > demo/tar/b.c
printf 'c\n' > demo/tar/d.txt
./tarext c demo/tar demo_c.tar
```

**Вывод**

```
Создан архив: demo_c.tar
Содержимое архива:
demo/tar/a.c
demo/tar/b.c
```

---

## Задание 9

**Задание**

Написать программу, которая заменяет в файле последовательности из 4 пробелов на символ табуляции. Входной и выходной файлы задаются аргументами.

**Код**

```bash
cat > spaces2tab <<'EOF'
#!/bin/bash
# spaces2tab: замена последовательностей из 4 пробелов на символ табуляции
if [ $# -ne 2 ]; then
    echo "Использование: $0 <входной_файл> <выходной_файл>" >&2
    exit 1
fi

sed 's/    /\t/g' "$1" > "$2"
EOF
chmod +x spaces2tab

mkdir -p demo
printf 'if (x) {\n    int y = 1;\n        z();\n}\n' > demo/spaces.txt
./spaces2tab demo/spaces.txt demo/spaces_tabs.txt
cat -T demo/spaces_tabs.txt
```

**Вывод**

```
if (x) {
^Iint y = 1;
^I^Iz();
}
```

---

## Задание 10

**Задание**

Написать программу, которая выводит названия всех пустых текстовых файлов в указанной директории. Директория передается в программу параметром.

**Код**

```bash
cat > emptyfiles <<'EOF'
#!/bin/bash
# emptyfiles: вывод названий всех пустых файлов в указанной директории
if [ $# -ne 1 ]; then
    echo "Использование: $0 <директория>" >&2
    exit 1
fi

find "$1" -maxdepth 1 -type f -empty -printf '%f\n'
EOF
chmod +x emptyfiles

mkdir -p demo/empty
printf '' > demo/empty/one.txt
printf '' > demo/empty/two.dat
printf 'data\n' > demo/empty/three.txt
./emptyfiles demo/empty
```

**Вывод**

```
one.txt
two.dat
```

