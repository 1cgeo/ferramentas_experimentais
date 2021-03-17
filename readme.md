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

## Botões
### 1- Calcula Azimute
Cria um campo na tabela de atributos da camada ativa, como armazenamento auxiliar, indicando o ângulo, no sentido horário, entre o norte e a direção da feição (considerando a *Oriented Minimum Bounding Box* da feição), recebe como entrada apenas camadas de linhas ou de polígonos.

### 2- Copia WKT 
Copia, para a área de transferência, a geometria das feições selecionadas em WKT.

### 3- Copia-Cola Geometria
Botão Copiar Geometria: copia, para uma variável interna do QGIS, a geometria da feição selecionada. Botão Colar Geometria:  substitui a geometria da feição selecionada de acordo com a geometria armazenada na variável interna. A geometria só é substituída se a camada da geometria de origem for do mesmo tipo geométrico da camada de destino. Copia e substitui apenas uma feição por vez.