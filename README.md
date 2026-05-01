# DOMME × LASZLO — Hub de Marcas Premium

## Deploy no Railway (3 passos)

### 1. Suba no GitHub
```bash
cd domme_deploy
git init
git add .
git commit -m "DOMME v8 - deploy"
git remote add origin https://github.com/SEU_USER/domme-app.git
git push -u origin main
```

### 2. No Railway
1. Acesse **railway.app** → New Project → Deploy from GitHub Repo
2. Selecione o repositório `domme-app`
3. Railway detecta o `Dockerfile` automaticamente
4. Clique em **Deploy**
5. Em **Settings → Networking** → gere um domínio público

### 3. Variáveis (opcional)
Em Settings → Variables, adicione:
```
PORT=8501
```
(O Dockerfile já define isso, mas alguns planos do Railway exigem explicitamente.)

---

## Estrutura do projeto
```
domme_deploy/
├── app.py                          Streamlit (4003 linhas, UI completa)
├── core/
│   ├── __init__.py
│   ├── auth.py                     RBAC (3 perfis)
│   ├── pricing.py                  Motor v3 + Renda Garantida
│   ├── data_loader.py              Lê do xlsx
│   ├── pdf_generator.py            Proposta em PDF
│   └── recommendations.py          Kits pré-curados + matching
├── data/
│   └── DOMME_Motor_v4.xlsx         589 SKUs Laszlo
├── .streamlit/config.toml          Config visual
├── Dockerfile                      Build container
├── Procfile                        Alternativa ao Dockerfile
├── railway.toml                    Config Railway
└── requirements.txt                Dependências Python
```

## Credenciais
| Usuário        | Senha        | Perfil   |
|----------------|--------------|----------|
| `camilla`      | `domme2025`  | ADMIN    |
| `laszlo`       | `laszlo2025` | FÁBRICA  |
| `cliente_demo` | `demo2025`   | CLIENTE  |

**Troque as senhas em `core/auth.py` antes do deploy.**

## Rodar local
```bash
pip install -r requirements.txt
streamlit run app.py
```
