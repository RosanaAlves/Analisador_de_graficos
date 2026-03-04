# test_imports.py
import sys
print("Python Path:")
for p in sys.path:
    print(f"  {p}")

print("\n" + "="*50)
print("TESTANDO IMPORTS")
print("="*50)

# Teste 1: Import direto de analisadores
try:
    from analisadores import AnalisadorBase
    print("✅ from analisadores import AnalisadorBase")
except Exception as e:
    print(f"❌ from analisadores: {e}")

# Teste 2: Import de scr.analisadores
try:
    from scr.analisadores import AnalisadorBase
    print("✅ from scr.analisadores import AnalisadorBase")
except Exception as e:
    print(f"❌ from scr.analisadores: {e}")

# Teste 3: Import específico
try:
    from scr.analisadores.base import AnalisadorBase
    print("✅ from scr.analisadores.base import AnalisadorBase")
except Exception as e:
    print(f"❌ from scr.analisadores.base: {e}")

# Teste 4: Import de utils
try:
    from scr.utils.imagem import carregar_imagem
    print("✅ from scr.utils.imagem import carregar_imagem")
except Exception as e:
    print(f"❌ from scr.utils.imagem: {e}")