# Esta primeira linha verifica se o pacote está instalado.
# Caso não esteja, irá prosseguir com a instalação
if(!require(foreign)) install.packages("foreign");library(foreign)
if(!require(knitr)) install.packages("knitr");library(knitr)
if(!require(lubridate)) install.packages("lubridate");library(lubridate)
if(!require(aweek)) install.packages("aweek");library(aweek)
if(!require(xts)) install.packages("xts");library(xts)
if(!require(plotly)) install.packages("plotly");library(plotly)
if(!require(ggTimeSeries)) install.packages("ggTimeSeries");library(ggTimeSeries)
if(!require(dplyr)) install.packages('dplyr'); library(dplyr)

# criando objeto do tipo dataframe (tabela) {`nindi`} com o banco de dados 
# {`NINDINET.dbf`}
nindi <- read.dbf('NINDINET.dbf', as.is = TRUE)

# Criando a tabela {`dengue`}
dengue <- nindi %>% 
  
  # Filtrando os registros de casos de dengue (CID = A90)
  filter(ID_AGRAVO == 'A90') %>% 
  
  # Criando novas colunas
  mutate(
    
    # Transformando a variável `DT_SIN_PRI` para data
    DT_SIN_PRI = ymd(DT_SIN_PRI),
    
    # Criando uma nova coluna chamada 'sem_epi', referente à semana
    # epidemiológica dos primeiros sintomas
    sem_epi = epiweek(DT_SIN_PRI),
    
    # Criando uma nova coluna chamada 'ano_epi', referente ao ano epidemiológico
    # dos primeiros sintomas
    ano_epi = epiyear(DT_SIN_PRI),
    
    # Criando uma nova coluna chamada 'mes', referente ao mês dos primeiros sintomas
    mes = month(DT_SIN_PRI),
    
    # Transformando a coluna `NU_ANO` no tipo numérico
    NU_ANO = as.numeric(NU_ANO)
  )

# criando gráfico de barras para avaliação temporal da dengue
graf_barras <- ggplot(data = dengue, aes(x = factor(NU_ANO))) +
  
  # Adicionando uma geometria de barras e definindo a cor do preenchimento
  # das barras
  geom_bar(fill = '#405599') + 
  
  # Definindo os títulos dos eixos x e y, rodapé, subtítulo e título do gráfico
  labs(
    title = 'Casos notificados de dengue em Rosas',
    subtitle = '2007 a 2012',
    caption = 'Fonte: SINAN',
    x = "Ano",
    y = "Casos"
  )

# Plotando o objeto `graf_barras`
print(graf_barras)

####################################################################

# Utilizando o objeto gráfico {`graf_barras`} salvo anteriormente
graf_barras + 
  
  # Alterando o tema do gráfico
  theme(
    
    # Alterando o texto do eixo x
    axis.text.x = element_text(
      angle = 45,         #  ângulo da orientação dos títulos
      hjust = 1,          #  definindo a posição horizontal do texto
      size = 11,          #  tamanho da letra
      color = '#202124' #  definindo a cor da letra
    ),
    
    # Alterando o texto do eixo y
    axis.text.y = element_text(
      angle = 0,          #  ângulo da orientação dos títulos
      hjust = 1,          #  definindo a posição horizontal do texto
      size = 11,          #  tamanho da letra
      color = '#202124'  #  definindo a cor da letra
    )     
  )

####################################################################

# Criando a tabela {`dengue_ano`}
dengue_ano <- dengue |>
  
  # Filtrando os registros cuja coluna `CS_SEXO` não tenha registros como `I`
  filter(CS_SEXO != 'I') |>
  
  # Agrupando as notificações pelo ano e sexo
  group_by(NU_ANO, CS_SEXO) |>
  
  # Contando a frequência de notificações
  count(name = 'n_casos')

####################################################################

dengue_ano <- dengue %>% 
  filter(CS_SEXO != 'I') %>% 
  select(NU_ANO, CS_SEXO, NU_NOTIFIC) %>% 
  group_by(NU_ANO, CS_SEXO) %>% 
  mutate( contagem = length(NU_NOTIFIC)) %>% 
  select(NU_ANO, CS_SEXO, contagem) %>% 
  group_by(NU_ANO, CS_SEXO)
View(dengue_ano)

####################################################################

graf_linhas <- ggplot(data = dengue_ano) +
  
  # Definindo argumentos estéticos com as variáveis usadas em x e em y
  # e definindo a variável usada para a cor dos pontos
  aes(x = NU_ANO, y = contagem, color = CS_SEXO) +
  
  # Adicionando a geometria de linhas e definindo espessura
  geom_line(size = 1.2) +
  
  # Definindo os títulos dos eixos x e y, rodapé, subtítulo e título do gráfico.
  # Para legenda, estamos definindo que o título será "Sexo"
  labs(
    title = 'Casos notificados de dengue em Rosas segundo sexo',
    subtitle = '2007 a 2012',
    caption = 'Fonte: SINAN',
    x = "Ano",
    y = "Casos",
    color = "Sexo"
  ) +
  
  # Definindo o tema base
  #theme_light() +
  
  # Alterando o tema do gráfico
  theme(
    
    # Alterando o texto do eixo x
    axis.text.x = element_text(
      angle = 0,
      hjust = 0.5,
      size = 10,
      color = '#202124'
    ),
    
    # Alterando o texto do eixo y
    axis.text.y = element_text(
      angle = 0,
      hjust = 1,
      size = 10,
      color = '#202124'
    )
  )

# Plotando o objeto `graf_linhas`
graf_linhas

# Utilizando o objeto gráfico {`graf_linhas`} salvo anteriormente
graf_linhas +
  
  # Adicionando a geometria de pontos e definindo o tamanho
  geom_point(size = 3) +
  
  # Alterando o tema do gráfico e posicionando a legenda na
  # parte inferior do gráfico
  theme(legend.position = 'left')

####################################################################

# Criando o objeto {`dengue_semana`}
dengue_semana <- dengue %>% 
  
  # Filtrando os registros com data de primeiros sintomas maior ou igual
  # a data de primeiro de janeiro de 2007.
  filter(DT_SIN_PRI  >= '2007-01-01') %>% 
  
  #Utilizando a função `mutate()` para criar novas colunas
  mutate(
    
    # Criando uma nova coluna chamada 'SEM_EPI` referente à semana
    # epidemiológica dos primeiros sintomas
    SEM_EPI = epiweek(DT_SIN_PRI),
    
    # Criando uma nova coluna chamada 'ANO_EPI` referente ao ano
    # epidemiológicos dos primeiros sintomas
    ANO_EPI = epiyear(DT_SIN_PRI),
    
    # Criando uma nova coluna chamada 'DT_INI_SEM` de data de início
    # da semana epidemiológica
    DT_INI_SEM = get_date(week = SEM_EPI, year = ANO_EPI)
    
  ) %>% 
  
  # Agrupando as notificações pelo ano epidemiológico, semana
  # epidemiológica e data de início da semana epidemiológica
  group_by(ANO_EPI, SEM_EPI, DT_INI_SEM) |>
  
  # Contando a frequência de notificações
  #length(name = 'n_casos')
  mutate(n_casos = length(NU_NOTIFIC))

####################################################################

graf_linhas2 <- ggplot(data = dengue_semana) + 
  aes(x = DT_INI_SEM, y = n_casos ) + 
  geom_line(color = '#995900', size = 1.2) + 
  labs(
    title = 'Casos notificados de dengue em Rosas',
    subtitle =  '2007 a 2012',
    caption = 'Fonte: SINAN',
    x = "Ano",
    y = "Casos"
  ) + 
  theme_classic() + 
  theme(
    axis.text.x = element_text(
      angle = 0,
      hjust = 1,
      size = 11,
      color = '#202124'
    ),
    axis.text.y = element_text(
      angle = 0,
      hjust = 1,
      size = 11,
      color = '#406199'
    ),
    
    plot.title = element_text(size = 16, color = 'darkblue'),
    plot.subtitle = element_text(size = 16, color = 'darkblue'),
    axis.title.x = element_text(size = 16, color = 'darkblue', face = 'bold'),
    axis.title.y = element_text(size = 16, color = 'darksalmon', face = 'bold')
  )
graf_linhas2

graf_linhas2 +
  
  # Arrumando o eixo x, definindo os intervalos dos marcadores de datas
  # (`date_breaks`) serão mostrados que, no caso, será uma sequência de
  # 6 em 6 meses
  scale_x_date(date_breaks = '6 months', date_labels = '%b/%Y') +
  
  # Alterando o tema do gráfico
  theme(
    # Alterando o texto do eixo x
    axis.text.x = element_text(
      angle = 90,
      hjust = 1,
      size = 14,
      color = 'grey32'
    ),
    
    # Alterando o texto do eixo y
    axis.text.y = element_text(
      hjust = 1,
      size = 14,
      color = 'grey32'
    )
  )

####################################################################

# Criando o objeto gráfico {`graf_barras_sobrepostas`}
graf_barras_sobrepostas <- ggplot(data = dengue_ano) +
  
  # Definindo argumentos estéticos com as variáveis usadas em x e em y
  # e a variável usada para o preenchimento das colunas
  aes(x = NU_ANO, y = n_casos, fill = CS_SEXO) +
  
  # Adicionando a geometria de colunas e definindo o tipo empilhado
  geom_col(position = 'stack') +
  
  # Definindo os títulos dos eixos x e y, rodapé, subtítulo e título do gráfico.
  # Para a legenda, estamos definindo o título como "Sexo"
  labs(
    title = 'Casos notificados de dengue em Rosas',
    subtitle =  '2007 a 2012',
    caption = 'Fonte: SINAN',
    x = "Ano",
    y = "Casos",
    fill = 'Sexo'
  ) +
  
  # Arrumando o eixo x, definindo quais os marcadores (`breaks`)
  # serão mostrados que, no caso, será uma sequência de 2007 a 2012,
  # referente aos anos.
  scale_x_continuous(breaks = 2007:2012) +
  
  # Definindo o tema base
  theme_light()

# Plotando o objeto `graf_barras_agrupadas`
graf_barras_sobrepostas
  
####################################################################

graf_barras_agrupadas <- ggplot(data = dengue_ano) +
  
  # Definindo argumentos estéticos com as variáveis usadas em x e em y
  # e a variável usada para o preenchimento das colunas
  aes(x = NU_ANO, y = n_casos, fill = CS_SEXO) +
  
  # Adicionando a geometria de colunas e definindo o tipo agrupado
  geom_col(position = 'dodge') +
  
  # Definindo o título da legenda das cores usadas para preenchimento
  # das colunas
  labs(fill = 'Sexo') +
  
  # Arrumando o eixo x, definindo quais os marcadores (`breaks`)
  # serão mostrados que, no caso, será uma sequência de 2007 a 2012,
  # referente aos anos.
  scale_x_continuous(breaks = 2007:2012) +
  
  # Definindo o tema base
  theme_light()

# Plotando o objeto `graf_barras_agrupadas`
graf_barras_agrupadas