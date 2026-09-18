# Página pública e adoção — 18/09/2026

## Implementado
- Oferta de 30 dias Individual sem cartão, com confirmação de e-mail.
- Demonstração compartilhada com o painel; dados de exemplo identificados.
- Navegação pública, ajuda, reenvio de ativação e perfil traduzido.
- FAQ e CTA de planos esclarecem que cadastro inicia o teste Individual.
- Canonical, descrição, Open Graph, robots e sitemap de páginas públicas.
- Noindex para páginas internas/cadastro via template base.
- Relatório agregado em /admin/product-metrics/, exclusivo de superusuários.

## Validação
- Layout inspecionado em Chromium desktop, 320/360/390/430/1280 px; sem overflow horizontal.
- Relatório não instala cookies de análise nem serviços externos; usa dados já existentes.
- Estatísticas refletem estado atual, não histórico de conversão. Ativação administrativa conta como ativa.

## Acompanhamento que depende de dados reais
- Depoimentos: obter texto e autorização dos participantes; não inventar resultados.
- Apresentação do criador: confirmar nome e qualificação antes de publicar.
- Analytics de visitantes/coortes/retorno: ainda não implementado. Selecionar escopo e provedor, verificar impacto de privacidade antes de instrumentar.
- Search Console: enviar sitemap quando houver acesso à propriedade verificada; não há envio neste commit.
- Lighthouse/Core Web Vitals e celulares físicos: complementam a verificação responsiva de laboratório.
- Google Play: esta entrega não altera release, preços, faturamento ou envia para revisão.
