# Política de Segurança — AI Document Analyzer

## ⚠️ Aviso sobre Dados Sensíveis (LGPD)

Este software envia o **conteúdo integral dos documentos** para a API do Google Gemini para processamento. Isso significa que:

- **Dados pessoais** presentes nos documentos (CPF, nomes, endereços, dados financeiros) serão transmitidos para os servidores do Google.
- O uso desta ferramenta com documentos que contêm dados pessoais pode estar sujeito à **Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018)**.
- **É responsabilidade do usuário** garantir que possui base legal para o tratamento desses dados e que o envio a APIs externas está em conformidade com as políticas de privacidade de sua organização.

### Recomendações

1. **Não armazene a API Key no código-fonte.** Use sempre o arquivo `.env` (que está no `.gitignore`).
2. **Avalie o uso de anonimização** antes de enviar documentos com dados pessoais sensíveis.
3. **Consulte o DPO de sua organização** antes de utilizar esta ferramenta em ambiente de produção com dados reais.
4. **Revise as políticas de uso de dados do Google Gemini** em: https://ai.google.dev/terms

## Relatando Vulnerabilidades

Se encontrar uma vulnerabilidade de segurança neste projeto, por favor:

1. **Não abra uma issue pública.** 
2. Envie um e-mail diretamente para o autor descrevendo o problema.
3. Aguarde uma resposta em até 48 horas.

## Versões Suportadas

| Versão | Suporte |
|--------|---------|
| 2.0.x  | ✅ Atual |
| 1.0.x  | ❌ Descontinuada |
