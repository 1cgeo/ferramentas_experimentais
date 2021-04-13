# Ferramentas experimentais

Conjunto de ferramentas experimentais em Python.

Algumas ferramentas estão disponibilizadas como *processing*, acessadas através da aba da **Caixa de Ferramentas de processamento** no QGIS.

Outras funções estão na forma de botões na barra de ferramentas do QGIS.




## Processings
### 1- Remover Camadas Vazias
Essa ferramenta, quando executada, remove as camadas vazias abertas no QGIS.

### 2- Atribuir SRC
A ferramenta permite que o usuário insira camadas e atribua um SRC, também escolhido pelo usuário, a elas. Também é possivel, através de uma caixa de seleção, atribuir o SRC a camadas com SRC inválido, não sendo necessário selecioná-las manualmente.

### 3- Exportar para *Shapefile*
O *processing*, ao ser executado, exporta camadas de um projeto para o formato *shapefile* seguindo as especificações de um shapefile modelo.

### 4- Ordenar Fluxo
Tem como parâmetro de entrada uma camada vetorial com geometria do tipo linha, com linhas já direcionadas e retorna uma cópia da camada com o campo "ordem" na tabela de atributos. A ordem é calculada da seguinte maneira: atribui-se 1 às linhas com conexão a apenas uma outra linha e para as outras linhas desconhecidas atribui-se a maior "ordem + 1" de outra linha conectada ao primeiro ponto dessa.

### 5 - Consistência entre Fluxo e Curva de Nível
Os parâmetros são: uma camada vetorial com geometria do tipo linha (camada de fluxo ou drenagem), o campo da tabela de atributos dessa camada correspondente a uma chave primaria (campo que identifica a linha), camada vetorial com geometria do tipo linha contendo as curvas de nível (camada de curva de nível), o campo da tabela de atributos dessa camada correspondente ao valor das cotas, o valor da equidistância entre as cotas. 

O *processing* detecta inconsistências na camada de drenagem em relação a camada contendo as curvas de nível. Se alguma inconsistência for detectada é gerada uma camada de pontos como saída apontando o local das inconsistências. Essa camada é gerada de "ordem" em "ordem" (de acordo com o calculado pelo *processing* **Ordenar Fluxo**), se, numa determinada ordem, for detectada inconsistência, o programa para, deixando de seguir para a procura na ordem seguinte e gera a camada de saída. Se não houver nenhuma inconsistência, retorna-se a mensagem "nenhuma inconsistência verificada" na janela de execução do *processing* como *feedback*.

No QGIS 3.16.4 no caso de uma curva de nível cujo vértice toca (usando *snap*) em apenas um vértice de uma drenagem, o *processing* nativo de interseção (que é o método usado para identificar as interseções entre a curva de nível e a drenagem) retorna 2 pontos com a mesma cota (cota da curva de nível que tocou a drenagem em um vértice), fazendo com o que o *processing* gere a camada de saída incluindo esses pontos como inconsistência (2 pontos com mesma cota em uma mesma linha de drenagem).

## Botões
### 1- Calcula Azimute
Cria um campo na tabela de atributos da camada ativa, como armazenamento auxiliar, indicando o ângulo, no sentido horário, entre o norte e a direção da feição (considerando a *Oriented Minimum Bounding Box* da feição), recebe como entrada apenas camadas de linhas ou de polígonos.

### 2- Copia WKT 
Copia, para a área de transferência, a geometria das feições selecionadas em WKT.

### 3- Copia-Cola Geometria
Botão Copiar Geometria: copia, para uma variável interna do QGIS, a geometria da feição selecionada. Botão Colar Geometria:  substitui a geometria da feição selecionada de acordo com a geometria armazenada na variável interna. A geometria só é substituída se a camada da geometria de origem for do mesmo tipo geométrico da camada de destino. Copia e substitui apenas uma feição por vez.