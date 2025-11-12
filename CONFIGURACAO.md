# Guia de Configuração - Strukturis

## 🔧 Configuração do Google Document AI

### Pré-requisitos

1. **Conta Google Cloud Platform (GCP)**
2. **Projeto GCP criado**
3. **Document AI API habilitada**
4. **Service Account com permissões**

### Passo 1: Criar Service Account

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Navegue até **IAM & Admin > Service Accounts**
3. Clique em **Create Service Account**
4. Preencha:
   - **Name**: `strukturis-docai`
   - **Description**: `Service account for Strukturis Document AI processing`
5. Adicione as seguintes roles:
   - `Document AI Editor`
   - `Cloud Storage Admin` (se usar GCS)
6. Clique em **Done**
7. Clique no service account criado
8. Vá em **Keys > Add Key > Create New Key**
9. Escolha **JSON** e baixe o arquivo

### Passo 2: Criar Processor no Document AI

1. Navegue até [Document AI](https://console.cloud.google.com/ai/document-ai)
2. Clique em **Create Processor**
3. Escolha **Form Parser** (recomendado para documentos estruturados)
4. Preencha:
   - **Processor name**: `strukturis-form-parser`
   - **Region**: `us` ou `eu` (escolha a mais próxima)
5. Clique em **Create**
6. Copie o **Processor ID** (formato: `1234567890abcdef`)

### Passo 3: Configurar Variáveis de Ambiente no Supabase

#### No Supabase Dashboard:

1. Acesse seu projeto Supabase
2. Vá em **Settings > Edge Functions > Secrets**
3. Adicione as seguintes variáveis:

```bash
# Google Cloud Project ID (encontrado no dashboard do GCP)
DOCAI_PROJECT_ID=seu-projeto-id

# Document AI Processor ID (copiado no passo anterior)
# IMPORTANTE: SEM ESPAÇOS EM BRANCO!
DOCAI_PROCESSOR_ID=1234567890abcdef

# Localização do processor (us, eu, asia-northeast1, etc)
DOCAI_LOCATION=us

# Credenciais do Service Account (conteúdo completo do JSON)
# Cole TODO o conteúdo do arquivo JSON baixado
GOOGLE_APPLICATION_CREDENTIALS_JSON={
  "type": "service_account",
  "project_id": "seu-projeto",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "strukturis-docai@seu-projeto.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

### Passo 4: Validar Configuração

#### Checklist de Validação:

- [ ] `DOCAI_PROJECT_ID` está definido e correto
- [ ] `DOCAI_PROCESSOR_ID` tem exatamente 16 caracteres hexadecimais (sem espaços!)
- [ ] `DOCAI_LOCATION` corresponde à região do processor
- [ ] `GOOGLE_APPLICATION_CREDENTIALS_JSON` é um JSON válido
- [ ] Service Account tem as permissões corretas
- [ ] Document AI API está habilitada no projeto

### Passo 5: Testar a Configuração

Após configurar, faça um teste:

1. Faça login na aplicação
2. Faça upload de um documento PDF ou imagem
3. Selecione as páginas para processar
4. Clique em "Processar"
5. Aguarde o processamento

Se tudo estiver correto, você verá:
- ✅ Processamento iniciado
- ✅ Texto extraído
- ✅ Tabelas identificadas (se houver)
- ✅ Relatório de confiabilidade gerado

## 🐛 Solução de Problemas Comuns

### Erro: "Processor not found"

**Causa**: `DOCAI_PROCESSOR_ID` incorreto ou com espaços em branco

**Solução**:
1. Verifique o Processor ID no Document AI console
2. Certifique-se de que NÃO há espaços antes ou depois do ID
3. Deve ter exatamente 16 caracteres hexadecimais (0-9, a-f)

### Erro: "Authentication failed"

**Causa**: Credenciais do Service Account inválidas

**Solução**:
1. Verifique se o JSON está completo e válido
2. Confirme que o Service Account tem as permissões corretas
3. Recrie as chaves se necessário

### Erro: "Project not found"

**Causa**: `DOCAI_PROJECT_ID` incorreto

**Solução**:
1. Verifique o Project ID no GCP Dashboard
2. Deve ser o ID do projeto, não o nome
3. Formato típico: `meu-projeto-123456`

### Erro: "API not enabled"

**Causa**: Document AI API não está habilitada

**Solução**:
1. Acesse [APIs & Services](https://console.cloud.google.com/apis/library)
2. Procure por "Document AI API"
3. Clique em "Enable"

### Erro: "File too large"

**Causa**: Arquivo excede 20MB (limite do Document AI)

**Solução**:
1. Reduza a resolução do PDF/imagem
2. Divida o documento em partes menores
3. Use compressão de PDF

### Erro: "Invalid token"

**Causa**: Sessão expirada ou token inválido

**Solução**:
1. Faça logout e login novamente
2. Limpe o cache do navegador
3. Verifique se o usuário está autenticado

## 📊 Limites e Quotas

### Document AI Quotas (Tier Gratuito):
- **1.000 páginas/mês** grátis
- **Tamanho máximo**: 20MB por arquivo
- **Formatos suportados**: PDF, PNG, JPEG, TIFF, GIF, BMP

### Supabase Storage:
- **1GB** de armazenamento grátis
- **2GB** de transferência/mês grátis

## 🔐 Segurança

### Boas Práticas:

1. **NUNCA** commite credenciais no Git
2. Use variáveis de ambiente para todas as credenciais
3. Rotacione as chaves do Service Account periodicamente
4. Limite as permissões ao mínimo necessário
5. Ative logs de auditoria no GCP
6. Use HTTPS em produção
7. Implemente rate limiting

## 🚀 Deploy

### Deploy das Edge Functions:

```bash
# Instalar Supabase CLI
npm install -g supabase

# Login no Supabase
supabase login

# Link ao projeto
supabase link --project-ref seu-projeto-ref

# Deploy das functions
supabase functions deploy process-document
supabase functions deploy ai-text-correction
supabase functions deploy ai-suggest-fill
```

### Configurar Secrets via CLI:

```bash
# Configurar todas as variáveis de uma vez
supabase secrets set \
  DOCAI_PROJECT_ID=seu-projeto-id \
  DOCAI_PROCESSOR_ID=1234567890abcdef \
  DOCAI_LOCATION=us \
  GOOGLE_APPLICATION_CREDENTIALS_JSON="$(cat service-account.json)"
```

## 📚 Recursos Adicionais

- [Documentação Document AI](https://cloud.google.com/document-ai/docs)
- [Guia de Processadores](https://cloud.google.com/document-ai/docs/processors-list)
- [Preços Document AI](https://cloud.google.com/document-ai/pricing)
- [Documentação Supabase Edge Functions](https://supabase.com/docs/guides/functions)
- [GitHub Issues](https://github.com/guiperlasca/Strukturis/issues)

## 💬 Suporte

Se precisar de ajuda:
1. Verifique os logs no Supabase Dashboard
2. Consulte este guia de configuração
3. Abra uma issue no GitHub
4. Entre em contato com o suporte

---

**Última atualização**: Novembro 2025  
**Versão**: 1.0.0