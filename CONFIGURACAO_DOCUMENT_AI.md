# Guia de Configuração do Google Document AI

## Problema Resolvido

O erro `Processor with id ' e1bdcd7c098ef0f1' not found` ocorria porque havia **espaços em branco** antes do Processor ID nas variáveis de ambiente.

## Solução Implementada

O código foi atualizado com:

1. **`.trim()` em todas as variáveis de ambiente** - Remove espaços automaticamente
2. **Validação de formato** - Verifica se o Processor ID é hexadecimal válido
3. **Logs detalhados** - Facilita identificação de problemas de configuração
4. **Retry logic** - Tenta novamente em caso de falhas transitórias
5. **Mensagens de erro claras** - Indica exatamente qual configuração está faltando

## Como Configurar as Variáveis de Ambiente no Supabase

### 1. Acesse o Painel do Supabase

1. Vá para [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Selecione seu projeto **Strukturis**
3. No menu lateral, clique em **Edge Functions**
4. Clique em **Manage** ou **Settings**

### 2. Configure as Variáveis de Ambiente

Adicione as seguintes variáveis:

#### DOCAI_PROJECT_ID
- **Valor**: Seu Project ID do Google Cloud (ex: `meu-projeto-123`)
- **Formato**: Apenas letras minúsculas, números e hífens
- **⚠️ Importante**: Não coloque espaços antes ou depois!

```
meu-projeto-123
```

#### DOCAI_PROCESSOR_ID
- **Valor**: ID do processador Document AI (ex: `e1bdcd7c098ef0f1`)
- **Formato**: Apenas caracteres hexadecimais (0-9, a-f)
- **⚠️ Importante**: Não coloque espaços antes ou depois!

```
e1bdcd7c098ef0f1
```

#### DOCAI_LOCATION
- **Valor**: Região do processador (ex: `us`, `eu`, `asia-northeast1`)
- **Padrão**: Se não for definido, usa `us`

```
us
```

#### GOOGLE_APPLICATION_CREDENTIALS_JSON
- **Valor**: Todo o conteúdo do arquivo JSON de credenciais da Service Account
- **Formato**: JSON válido
- **⚠️ Importante**: Cole o JSON completo, incluindo as chaves `{}`

```json
{
  "type": "service_account",
  "project_id": "meu-projeto-123",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n",
  "client_email": "minha-conta@meu-projeto.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

### 3. Como Obter as Credenciais do Google Cloud

#### Passo 1: Criar/Acessar Projeto no Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Anote o **Project ID**

#### Passo 2: Ativar a API do Document AI

1. No menu lateral, vá para **APIs & Services** > **Library**
2. Busque por "Cloud Document AI API"
3. Clique em **Enable**

#### Passo 3: Criar um Processador

1. No menu lateral, vá para **Document AI** > **Processors**
2. Clique em **Create Processor**
3. Selecione **Form Parser** (recomendado para extrair tabelas e formulários)
4. Escolha a região (ex: `us`, `eu`)
5. Anote o **Processor ID** (aparece na URL: `.../processors/SEU_PROCESSOR_ID`)

#### Passo 4: Criar Service Account

1. Vá para **IAM & Admin** > **Service Accounts**
2. Clique em **Create Service Account**
3. Nome: `strukturis-docai` (ou outro nome)
4. Clique em **Create and Continue**
5. Adicione a role: **Document AI API User**
6. Clique em **Done**

#### Passo 5: Criar Chave JSON

1. Clique na Service Account criada
2. Vá para a aba **Keys**
3. Clique em **Add Key** > **Create new key**
4. Selecione **JSON**
5. Clique em **Create** - o arquivo JSON será baixado
6. **Abra o arquivo e copie TODO o conteúdo** para a variável `GOOGLE_APPLICATION_CREDENTIALS_JSON`

### 4. Verificar Configuração

Após configurar todas as variáveis:

1. No Supabase, vá para **Edge Functions**
2. Selecione a função `process-document`
3. Clique em **Logs**
4. Faça upload de um documento de teste
5. Observe os logs - deve aparecer:

```
=== Document AI Configuration ===
Credentials present: true
Project ID: meu-projeto-123
Location: us
Processor ID: e1bdcd7c098ef0f1
Processor ID (hex check): true
✓ Document AI configuration valid
```

## Solução de Problemas

### Erro: "DOCAI_PROCESSOR_ID has invalid format"

**Causa**: O Processor ID contém caracteres inválidos ou espaços

**Solução**:
1. Verifique se o ID contém apenas letras a-f e números 0-9
2. Remova espaços antes e depois
3. Copie diretamente da URL do processador no Google Cloud

### Erro: "Processor with id 'XXX' not found"

**Causa**: O Processor ID está incorreto ou o processador foi deletado

**Solução**:
1. Acesse o [Document AI Console](https://console.cloud.google.com/ai/document-ai/processors)
2. Verifique se o processador existe
3. Copie o ID correto da URL
4. Verifique se está usando o projeto correto

### Erro: "GOOGLE_APPLICATION_CREDENTIALS_JSON is not valid JSON"

**Causa**: O JSON das credenciais está malformado

**Solução**:
1. Baixe novamente o arquivo de credenciais do Google Cloud
2. Abra em um editor de texto
3. Copie TODO o conteúdo (incluindo `{` e `}`)
4. Cole na variável de ambiente sem modificações

### Erro: "OAuth failed"

**Causa**: As credenciais não têm permissão ou estão inválidas

**Solução**:
1. Verifique se a Service Account tem a role **Document AI API User**
2. Crie uma nova chave JSON se a atual estiver expirada
3. Verifique se a API do Document AI está ativada no projeto

### Erro: "File too large"

**Causa**: O arquivo excede 20MB (limite do Document AI)

**Solução**:
1. Comprima o PDF usando ferramentas online
2. Reduza a resolução de imagens antes de converter para PDF
3. Divida o documento em partes menores

## Melhorias Implementadas no Código

### 1. Validação Rigorosa

```typescript
function getDocAIConfig() {
  // Remove espaços automaticamente
  const processorId = Deno.env.get('DOCAI_PROCESSOR_ID')?.trim();
  
  // Valida formato hexadecimal
  if (!/^[a-f0-9]+$/.test(processorId)) {
    errors.push(`Invalid processor ID format: "${processorId}"`);
  }
}
```

### 2. Logs Detalhados

Todos os passos do processamento agora têm logs:

```
=== Process Document Request Started ===
✓ User authenticated: abc123
✓ File downloaded: 2.5MB
✓ Base64 conversion complete
✓ OAuth token obtained
✓ Document AI processing successful
✓ Page 1: ok, confidence 92%, 2 tables, 5 fields
=== Processing Summary ===
Readability Confidence: 92%
Page Success Rate: 100%
Tables Detected: 2
Fields Detected: 5
```

### 3. Retry Logic

Tentativas automáticas em caso de falha transitória:

```typescript
await retryWithBackoff(async () => {
  return await fetch(endpoint, {...});
}, 2, 2000); // 2 tentativas, delay de 2s
```

### 4. Otimização de Performance

Conversão base64 otimizada para arquivos grandes:

```typescript
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  const chunkSize = 16384; // 16KB chunks
  const chunks: string[] = [];
  
  for (let i = 0; i < bytes.length; i += chunkSize) {
    chunks.push(String.fromCharCode(...bytes.slice(i, i + chunkSize)));
  }
  
  return btoa(chunks.join(''));
}
```

## Próximos Passos

1. **Teste a configuração** fazendo upload de um documento
2. **Monitore os logs** no Supabase Edge Functions
3. **Ajuste as variáveis** se necessário
4. **Verifique os resultados** na interface

## Suporte

Se continuar com problemas:

1. Verifique os logs no Supabase (Edge Functions > process-document > Logs)
2. Confira se todas as variáveis estão definidas corretamente
3. Teste com um arquivo pequeno (menos de 1MB) primeiro
4. Verifique se há créditos disponíveis no Google Cloud

---

**Última atualização**: 2025-11-11  
**Versão do código**: dfcdd910c5d4493c957c840a9d5b731a96bb7cfa