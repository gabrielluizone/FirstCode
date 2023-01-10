# Importaçãode Bibliotecas
if(!require(tidyverse)) install.packages("tidyverse");library(tidyverse)

# Importando o banco de dados {`vigitel_2015.csv`}
# e armazenando os dados no objeto `vigitel`
vigitel <- read_csv2('vigitel_2015.csv')

# Visualizando a estrutura do objeto {`vigitel`}
glimpse(vigitel)

vigitel <- vigitel |>
  # Transformando os valores da coluna "fuma" para "sim" e "não" apenas
  mutate( fuma = if_else(fuma == 'não', 'não', 'sim') )

vigitel <- vigitel %>% 
  mutate( fuma = if_else(fuma == 'não', 'não', 'sim') )

# Grid dos gráficos
par(mfrow = c(2, 2))

# Gráfico 1
plot(
  x = vigitel$peso,
  y = vigitel$altura,
  pch = 19,
  col = 'blue',
  cex = 0.3,
  main = 'Gráfio 01 | Pontos Peso pela Altura',
  xlab = 'Peso',
  ylab = 'Altura'
)
abline(v = mean(vigitel$peso, na.rm = T), col = '#212124', lty = 2, lwd = 3)
abline(h = mean(vigitel$altura, na.rm = T), col = 2, lty = 2, lwd = 3)

# Gráfico 2
boxplot(
  vigitel$idade ~ vigitel$sexo,
  col = c('#00ffff', '#ff0000'),
  main = 'Gráfico 2 | Boxplot Idade / Sexo',
  xlab = 'Idade',
  ylab = 'Sexo'
)

# Gráfico 3
hist(
  x = vigitel$peso,
  col = "salmon",
  main = "Gráfico 3. Histograma Peso",
  xlab = "Peso",
  ylab = "Frequência"
)

# Gráfico 4
barplot(prop.table(table(vigitel$fuma)),
        col = c("steelblue", "orange"),
        main = "Gráfico 4.Proporção de Fumantes")