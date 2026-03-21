# Analisador de Processos Jurídicos com Gemini AI

## 📖 Sobre o Projeto
O Analisador de Processos Jurídicos é uma aplicação de desktop desenvolvida em Python que utiliza o poder da Inteligência Artificial generativa do Google Gemini para automatizar a análise e extração de dados de documentos processuais. A ferramenta lê arquivos `.pdf` e `.txt` contendo peças jurídicas, como petições ou apelações, e gera uma planilha estruturada com as informações mais relevantes, otimizando o tempo e a eficiência na triagem de processos.

Este projeto foi criado como uma demonstração prática de habilidades em desenvolvimento de software, integração de APIs de IA e criação de interfaces gráficas, sendo uma peça central do meu portfólio profissional.

## ✨ Funcionalidades Principais
- **Interface Gráfica Intuitiva**: Interface limpa e moderna construída com a biblioteca CustomTkinter.
- **Suporte a Múltiplos Formatos**: Capacidade de processar tanto arquivos de texto (`.txt`) quanto documentos PDF (`.pdf`).
- **Análise com IA**: Integração direta com a API do Google Gemini (2.5 Flash) para realizar a extração e classificação inteligente dos dados.
- **Exportação de Dados**: Salva os resultados em um arquivo `.csv` formatado, pronto para ser utilizado em planilhas ou sistemas de banco de dados.
- **Processamento Assíncrono**: A análise dos documentos é executada em uma thread separada para garantir que a interface do usuário permaneça responsiva durante o processamento.
- **Integração com Power Automate**: Planejamento e suporte automação. "Copiar conteúdo do agravo.txt ou apelação.txt e colar em um novo Fluxo".

## 📸 Demonstração
1. Tela Inicial do Programa.
<img width="862" height="691" alt="image" src="https://github.com/user-attachments/assets/b3c33938-1f60-4799-9a79-2ed98c37afa1" />
3. Escolha do Processo a ser Analisado.
5. PDF em Processo de Análise.
<img width="862" height="691" alt="image" src="https://github.com/user-attachments/assets/ac6ce69f-8233-462e-9dfd-4f9e52f56bf0" />
7. Processo Baixado em CSV.
<img width="844" height="686" alt="image" src="https://github.com/user-attachments/assets/d93ad138-94ec-42b4-8abd-4bf96f21e422" />


## 🛠️ Tecnologias Utilizadas
- **Python 3.8+**
- **CustomTkinter**: Para a criação da interface gráfica.
- **Google Generative AI**: Biblioteca oficial para interagir com a API do Gemini.
- **PyPDF2**: Para a extração de texto de arquivos PDF.
- **python-dotenv**: Para o gerenciamento seguro de chaves de API.

## 🚀 Instalação e Execução
Siga os passos abaixo para executar o projeto em seu ambiente local.

### 1. Pré-requisitos
- Python 3.8 ou superior instalado.
- Uma chave de API do Google Gemini. Você pode obter uma gratuitamente no Google AI Studio.

### 2. Clonar o Repositório
```bash
git clone https://github.com/Enockjoao/PJE_AI_Processor.git
cd PJE_AI_Processor
```

### 3. Instalar as Dependências
É altamente recomendável criar um ambiente virtual para isolar as dependências do projeto.

Criar um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
```

Ativar o ambiente virtual:
- **No Windows:**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **No macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

Instalar as bibliotecas necessárias:
```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente
Crie um arquivo chamado `.env` na raiz do projeto, copiando o conteúdo do arquivo `.env.example`. Em seguida, insira sua chave da API do Gemini.

Arquivo `.env`:
```env
GEMINI_API_KEY="SUA_CHAVE_DE_API_AQUI"
GEMINI_MODEL="gemini-2.5-flash"
```

### 5. Executar a Aplicação
Com tudo configurado, execute o script principal para iniciar a interface.
```bash
python main.py
```

## ⚙️ Como Usar
1. Com a aplicação aberta, clique no botão "Selecionar Arquivo".
2. Escolha um arquivo de processo no formato `.pdf` ou `.txt`.
3. O nome do arquivo aparecerá na tela. Clique no botão "Iniciar Análise e Salvar".
4. Aguarde o processamento. O status será atualizado na parte inferior da janela.
5. Ao final, uma janela de "Salvar como..." será aberta. Escolha o local e o nome para o seu arquivo `.csv`.
6. Pronto! Seu processo foi analisado e os dados foram salvos.

## 🔧 Como Customizar a Análise (Prompt)
A inteligência da extração reside no "prompt" enviado à API. Você pode customizar completamente o que a IA deve extrair e como ela deve formatar a saída.

- Você pode criar e modificar arquivos de templates dinâmicos na pasta `src/prompts/` (ex: `Triagem.txt`, `contratos.txt`).
- No uso via terminal/script simples (`api_handler.py`), localize a variável `prompt` dentro da função `analyze_with_gemini` e altere as instruções ou regras de extração para atender às suas necessidades.

### Para Iniciar pelo Power Automate
Consulte a documentação em: `PowerAutomate.md`

---

## ⚖️ Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 👨‍💻 Autor
Feito por **Enock**  
LinkedIn: (https://www.linkedin.com/in/joao-victor-enock-972b682b9/)
