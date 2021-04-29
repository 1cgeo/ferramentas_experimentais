# Ferramentas experimentais

Conjunto de ferramentas experimentais para verificar a aplicabilidade na produção de geoinformação.

Algumas ferramentas estão disponibilizadas como *processing*, acessadas através da aba da **Caixa de Ferramentas de processamento** no QGIS.

Outras funções estão na forma de botões na barra de ferramentas do QGIS.

## Processings
### 1- Remover Camadas Vazias
Essa ferramenta, quando executada, remove as camadas vazias abertas no QGIS.

### 2- Atribuir SRC
A ferramenta permite que o usuário insira camadas e atribua um SRC, também escolhido pelo usuário, a elas. Também é possivel, através de uma caixa de seleção, atribuir o SRC a camadas com SRC inválido, não sendo necessário selecioná-las manualmente.

### 3- Exportar para *Shapefile* no padrão MGCP
O *processing*, ao ser executado, exporta camadas de um projeto para o formato *shapefile* seguindo as especificações de um shapefile modelo.

### 4- Ordenar Trecho de Drenagem
Tem como parâmetro de entrada uma camada vetorial com geometria do tipo linha, com linhas já direcionadas e retorna uma cópia da camada com o campo "ordem" na tabela de atributos. A ordem é calculada da seguinte maneira: atribui-se 1 às linhas com conexão a apenas uma outra linha e para as outras linhas desconhecidas atribui-se a maior "ordem + 1" de outra linha conectada ao primeiro ponto dessa.

*É necessário que a camada do trecho de drenagem esteja direcionada*

### 5 - Consistência entre Trecho de Drenagem e Curva de Nível
Os parâmetros são: uma camada vetorial com geometria do tipo linha (camada de fluxo ou drenagem), o campo da tabela de atributos dessa camada correspondente a uma chave primaria (campo que identifica a linha), camada vetorial com geometria do tipo linha contendo as curvas de nível (camada de curva de nível), o campo da tabela de atributos dessa camada correspondente ao valor das cotas, o valor da equidistância entre as cotas. 

O *processing* detecta inconsistências na camada de drenagem em relação a camada contendo as curvas de nível. Se alguma inconsistência for detectada é gerada uma camada de pontos como saída apontando o local das inconsistências. Essa camada é gerada de "ordem" em "ordem" (de acordo com o calculado pelo *processing* **Ordenar Fluxo**), se, numa determinada ordem, for detectada inconsistência, o programa para, deixando de seguir para a procura na ordem seguinte e gera a camada de saída. Se não houver nenhuma inconsistência, retorna-se a mensagem "nenhuma inconsistência verificada" na janela de execução do *processing* como *feedback*.

No QGIS 3.16.4 no caso de uma curva de nível cujo vértice toca (usando *snap*) em apenas um vértice de uma drenagem, o *processing* nativo de interseção (que é o método usado para identificar as interseções entre a curva de nível e a drenagem) retorna 2 pontos com a mesma cota (cota da curva de nível que tocou a drenagem em um vértice), fazendo com o que o *processing* gere a camada de saída incluindo esses pontos como inconsistência (2 pontos com mesma cota em uma mesma linha de drenagem).

### 6 - Identificar Geometria Inválida
Tem como parâmetro camadas vetorias e *string* contendo o nome do campo contendo chave primária (padrão = id), ao ser executado retorna, no log, o campo primário das feições que possuem geometria invalida e suas respectivas camadas. Verifica-se se a feição apresenta:
- Geometria diferente de MultiPoint, MultiLineString ou MultiPolygon
- Geometria nula ou vazia
- Outro caso de geometria invalida, poligonos que não fecham, linhas com apenas 1 ponto, polígonos com menos de 3 pontos, etc

### 7 - Identificar fundo de vale incorreto
Parâmetros necessários:
- Camada de curva de nível
- Camada de trecho de drenagem
- Tamanho do segmento sobre a linha (D1): Distância partir do ponto de interseçào entre uma curva e uma drenagem, sobre a curva de nível
- Tolerância para a projeçã0 do ponto (D2): Distância máxima entre a interseção (curva de nível vs trecho de drenagem) e o segmento gerado pelos extremos do arco do item anterior
A figura a seguir descreve as medidas D1 e D2 tomadas como parâmetro no algoritmo.
<p align="center">
  <img src="icons/exp7.PNG">
</p>

### 8 - Identificar Geometria com Multiplas Partes
Recebe uma lista de camadas e verifica se alguma feição tem geometria contendo mais de uma parte, por exemplo, uma camada de pontos com uma feição cuja geoemtria é mais de um ponto. Retorna camadas de inconsistência para cada tipo de geometria, se não for encontrada nenhuma inconsistência de um determinado tipo de geometria, não haverá retorno daquele tipo de geometria

### 9 - Identificar *Holes* Menores que Tolerância
Recebe camada de poligonos e um valor para tolerância, retorna camada de polígonos dos *holes* com área menor que a tolerância determinada 

### 10 - Identificar Feições Menores que Tolerância
Recebe uma lista de camadas vetoriais, uma tabela CSV contendo duas colunas: nome, (da camada), tamanho (máximo das feições), nessa ordem, necessariamente, e uma camada do tipo polígono contendo a moldura. Verifica-se então quais feições são menores que o tamanho determinado para cada camada e retorna-se aquelas que estão completamente dentro das molduras.

### 11 - Identificar Linhas Soltas Menores que Tolerância
Recebe uma lista de camadas vetoriais (linhas), uma tabela CSV contendo duas colunas: nome (da camada), tamanho (máximo das feições), nessa ordem, necessariamente, e uma camada do tipo polígono contendo a moldura. Verifica-se então quais linhas soltas são menores que o tamanho determinado para cada camada e retorna-se aquelas que estão completamente dentro das molduras.

### 12 - Identificar Linhas Próximas à Moldura
Recebe uma lista de camadas vetoriais (linhas), um número indicando o valor máximo para a distância da linha à borda, e uma camada do tipo polígono contendo a moldura. Verifica-se então quais linhas soltas estão a uma distância menor do que a especificada da borda e retorna-se aquelas que estão completamente dentro das molduras.

### 13 - Identificar Descontinuidade em Linhas
Recebe uma camada vetorial do tipo linha, os campos a serem verificados e um valor de tolerância para desvio da linha. Verifica-se se houve mudança no valor dos campos a serem verificados entre duas linhas cujo ângulo entre elas diferencie, no máximo, do valor de tolerância em relação a 180 graus. Por exemplo, se o valor de tolerância for 10, apenas linhas cujo menor angulo entre elas esteja no intervalo de (170,180) terão os campos comparados.


## Botões
### 1- Calcula Azimute
Cria um campo na tabela de atributos da camada ativa, como armazenamento auxiliar, indicando o ângulo, no sentido horário, entre o norte e a direção da feição (considerando a *Oriented Minimum Bounding Box* da feição), recebe como entrada apenas camadas de linhas ou de polígonos.

### 2- Copia WKT 
Copia, para a área de transferência, a geometria das feições selecionadas em WKT.

### 3- Copia-Cola Geometria
Botão Copiar Geometria: copia, para uma variável interna do QGIS, a geometria da feição selecionada. Botão Colar Geometria:  substitui a geometria da feição selecionada de acordo com a geometria armazenada na variável interna. A geometria só é substituída se a camada da geometria de origem for do mesmo tipo geométrico da camada de destino. Copia e substitui apenas uma feição por vez.

### 4- Corta início da linha
Dado um ou mais linhas selecionadas, a ferramenta corta o ínicio do linha em uma distância configurável.