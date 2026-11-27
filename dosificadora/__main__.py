import sys
from pathlib import Path


if __name__ == "__main__":
    if not __package__:
        # Al ejecutar este archivo directamente, Python busca desde dosificadora/.
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from dosificadora.interfaz import main

    raise SystemExit(main())
