import sqlite3
import csv

arquivo_diff = 'Violations_diffs\\conflicts_with_onlyReqProp_repairs.csv'
arquivo_correcoes = 'conflicts_with_onlyReqProp_correcoesTESTE1.csv'

def adicionar_correcao(arquivo, correcao):
    with open(arquivo, 'a', newline='', encoding='utf-8') as arq:
        escritor = csv.writer(arq)
        escritor.writerow(correcao)

def normalizar_url(url):
    if('http://www.wikidata.org/prop/direct/' in url):
        return url.replace('http://www.wikidata.org/prop/direct/', 'http://www.wikidata.org/entity/')
    
    elif('http://www.wikidata.org/prop/qualifier/' in url):
        return url.replace('http://www.wikidata.org/prop/qualifier/', 'http://www.wikidata.org/entity/')
    
    elif('http://www.wikidata.org/prop/' in url):
        return url.replace('http://www.wikidata.org/prop/', 'http://www.wikidata.org/entity/')
    else:
        return url

def testar_correcoes():
    conexao = sqlite3.connect("constraint.db")
    cursor = conexao.cursor()
    constraint = 'conflicts_with'

    only = 'True'

    consulta_deletados = """
        SELECT *
        FROM dados_removidos AS dr
        WHERE constraint_instance IN (
            SELECT constraint_instance
            FROM dados_removidos
            WHERE constraint_predicate_parameters = 'http://www.wikidata.org/prop/statement/P2302'
            AND constraint_name = ? 
            AND NOT EXISTS (
                SELECT 1
                FROM constraint_instances_2023 AS ci
                WHERE ci.constraint_predicate_parameters = dr.constraint_predicate_parameters
                    AND ci.constraint_name = dr.constraint_name
                    AND ci.property = dr.property
                    AND ci.constraint_object_parameters = dr.constraint_object_parameters
            )
        );
    """ 

    cursor.execute(consulta_deletados, (constraint,))
    resultados_deletados = cursor.fetchall()

    if(constraint == 'conflicts_with' or constraint == 'item_requires_statement'):
        if(only == 'False'):
            consulta_deletados = """
                SELECT 
                    dr.constraint_instance, 
                    dr.property, 
                    da1.constraint_object_parameters AS object_p2306, 
                    da2.constraint_object_parameters AS object_p2305
                FROM 
                    dados_removidos AS dr
                LEFT JOIN 
                    dados_removidos AS da1 
                    ON dr.constraint_instance = da1.constraint_instance 
                    AND da1.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'
                    AND da1.constraint_name = ?
                LEFT JOIN 
                    dados_removidos AS da2 
                    ON dr.constraint_instance = da2.constraint_instance 
                    AND da2.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2305'
                    AND da2.constraint_name = dr.constraint_name
                WHERE 
                    dr.constraint_predicate_parameters = 'http://www.wikidata.org/prop/statement/P2302'
                    AND dr.constraint_name = da1.constraint_name
                    AND NOT EXISTS (
                        SELECT 1
                        FROM constraint_instances_2023 AS ci
                        WHERE ci.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306' -- mudei para p2306 ao inves de p2305
                        AND ci.constraint_name = dr.constraint_name
                        AND ci.property = dr.property
                        AND ci.constraint_object_parameters = da1.constraint_object_parameters
                    );
                """ 
            hashmap_sem_valor_deletados = {}
            hashmap_com_valor_deletados = {}
            propriedades_deletados = []

            cursor.execute(consulta_deletados, (constraint,))
            resultados_deletados = cursor.fetchall()

            for resultado in resultados_deletados:
                propriedade = resultado[1]
                propriedades_deletados.append(propriedade)
                propriedade_proibida = resultado[2]
                valor = resultado[3]
                
                if propriedade_proibida and valor is not None:
                    if propriedade not in hashmap_com_valor_deletados:
                        hashmap_com_valor_deletados[propriedade] = []
                    hashmap_com_valor_deletados[propriedade].append((propriedade_proibida, valor))
                
                elif propriedade_proibida is not None and valor is None:
                    if propriedade not in hashmap_sem_valor_deletados:
                        hashmap_sem_valor_deletados[propriedade] = []
                    hashmap_sem_valor_deletados[propriedade].append(propriedade_proibida)  

        else:
            consulta_deletados = """
                SELECT dr.constraint_instance, dr.property, da1.constraint_object_parameters AS object_p2306
            FROM 
                dados_removidos AS dr
            LEFT JOIN 
                dados_removidos AS da1 
                ON dr.constraint_instance = da1.constraint_instance 
                AND da1.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'
                AND da1.constraint_name = ?
            WHERE 
                dr.constraint_predicate_parameters = 'http://www.wikidata.org/prop/statement/P2302'
                AND dr.constraint_name = da1.constraint_name
                AND NOT EXISTS (
                    SELECT 1
                    FROM constraint_instances_2023 AS ci
                    WHERE ci.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'
                    AND ci.constraint_name = dr.constraint_name
                    AND ci.property = dr.property
                    AND ci.constraint_object_parameters = da1.constraint_object_parameters
                );

                """ 
            hashmap_sem_valor_deletados = {}
            propriedades_deletados = []

            cursor.execute(consulta_deletados, (constraint,))
            resultados_deletados = cursor.fetchall()

            for resultado in resultados_deletados:
                propriedade = resultado[1]
                propriedades_deletados.append(propriedade)
                propriedade_proibida = resultado[2]
                        
                if propriedade_proibida is not None:
                    if propriedade not in hashmap_sem_valor_deletados:
                        hashmap_sem_valor_deletados[propriedade] = []
                    hashmap_sem_valor_deletados[propriedade].append(propriedade_proibida)  

    consulta_depreciados = """
        SELECT *
        FROM constraint_instances_2023
        WHERE constraint_instance IN (
            SELECT constraint_instance
            FROM dados_adicionados
            WHERE constraint_name = ? AND
                constraint_predicate_parameters = 'http://wikiba.se/ontology#rank' AND
                constraint_object_parameters = 'http://wikiba.se/ontology#DeprecatedRank'
        );
    """   
       
    cursor.execute(consulta_depreciados, (constraint,))
    resultados_depreciados = cursor.fetchall()
    if constraint == 'conflicts_with' or constraint == 'item_requires_statement':
        consulta_depreciados = """
        SELECT DISTINCT
            ci.constraint_instance,
            ci.property,
            da1.constraint_object_parameters AS object_p2306,
            da2.constraint_object_parameters AS object_p2305
        FROM 
            constraint_instances_2023 ci
            INNER JOIN constraint_instances_2023 da3 
                ON ci.constraint_instance = da3.constraint_instance 
                AND ci.constraint_predicate_parameters = 'http://wikiba.se/ontology#rank'
                AND ci.constraint_object_parameters = 'http://wikiba.se/ontology#DeprecatedRank'
                AND ci.constraint_name = ?
            LEFT JOIN constraint_instances_2023 da1 
                ON ci.constraint_instance = da1.constraint_instance 
                AND da1.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'
                AND da1.constraint_name = ci.constraint_name
            LEFT JOIN constraint_instances_2023 da2 
                ON ci.constraint_instance = da2.constraint_instance 
                AND da2.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2305'
                AND da2.constraint_name = ci.constraint_name

        """  
        hashmap_depreciados_sem_valor = {}
        hashmap_depreciados_com_valor = {}
        propriedades = []

        cursor.execute(consulta_depreciados, (constraint,))
        resultados_depreciados = cursor.fetchall()

        for resultado in resultados_depreciados:
            propriedade = resultado[1]
            propriedades.append(propriedade)
            propriedadeReq = resultado[2]
            valor = resultado[3]
            
            if propriedade not in hashmap_depreciados_com_valor:
                hashmap_depreciados_com_valor[propriedade] = []
            if propriedade not in hashmap_depreciados_sem_valor:
                hashmap_depreciados_sem_valor[propriedade] = []

            if propriedadeReq and valor is not None:
                hashmap_depreciados_com_valor[propriedade].append((propriedadeReq, valor))
            elif propriedadeReq is not None and valor is None:
                hashmap_depreciados_sem_valor[propriedade].append(propriedadeReq)
        
    
    aux = {}
    cursor.execute("SELECT distinct property, COUNT(DISTINCT constraint_instance) FROM constraint_instances_2023 WHERE constraint_name = ? GROUP BY property", (constraint,))
    resultados_aux_depreciados = cursor.fetchall()
    for resultado in resultados_aux_depreciados:
        propriedade = resultado[0]
        quant_instancia = resultado[1]
        aux[propriedade] = quant_instancia    

    # Exceção
    prop_obj_map = {}
    cursor.execute("SELECT property, constraint_object_parameters FROM dados_adicionados WHERE constraint_name = ? AND constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2303'", (constraint,))
    resultados_excecao = cursor.fetchall()
    for resultado in resultados_excecao:
        propriedade = resultado[0]
        entidade = resultado[1]
        if propriedade in prop_obj_map:
            prop_obj_map[propriedade].append(entidade)
        else:
            prop_obj_map[propriedade] = [entidade]

    # ESPECIFICA ONE_OF
    if(constraint == 'one_of'):
        cursor.execute("SELECT property, constraint_object_parameters FROM dados_adicionados WHERE constraint_name = ? AND constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2305'", (constraint,))
        resultados_oneOf = cursor.fetchall()
        oneOf = {}
        for resultado in resultados_oneOf:
            propriedade = resultado[0]
            objeto = resultado[1]
            if propriedade in oneOf:
                oneOf[propriedade].append(objeto)
            else:
                oneOf[propriedade] = [objeto]

    # ESPECIFICA NONE_OF
    if(constraint == 'none_of'):
        consulta_none_of = """  
        SELECT property, constraint_object_parameters 
        FROM dados_removidos AS dr
        WHERE constraint_name = 'none_of'
        AND constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2305'
        
        AND NOT EXISTS (
            SELECT 1
            FROM dados_adicionados AS da
            WHERE da.property = dr.property
            AND da.constraint_name = 'none_of'
            AND da.constraint_object_parameters = dr.constraint_object_parameters
        );
        """  
        cursor.execute(consulta_none_of)
        resultados_noneOf = cursor.fetchall()
        noneOf = {}
        for resultado in resultados_noneOf:
            propriedade = resultado[0]
            objeto = resultado[1] 
            if propriedade in noneOf:
                noneOf[propriedade].append(objeto)
            else:
                noneOf[propriedade] = [objeto]

    # ESPECIFICA ALLOWED_QUALIFIERS
    if(constraint == 'allowed_qualifiers'):
        cursor.execute("SELECT property, constraint_object_parameters FROM dados_adicionados WHERE constraint_name = ? AND constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'",(constraint,))
        resultados_allowed_qualifiers = cursor.fetchall()
        allowedQualifiers = {}
        for resultado in resultados_allowed_qualifiers:
            propriedade = resultado[0]
            objeto = resultado[1]
            if propriedade in allowedQualifiers:
                allowedQualifiers[propriedade].append(objeto)
            else:
                allowedQualifiers[propriedade] = [objeto] 

    #  ESPECIFICA DO REQUIRED_QUALIFIER
    if(constraint == 'required_qualifiers'):
        consulta_req_qualifier = """  
        SELECT property, constraint_object_parameters 
        FROM dados_removidos AS dr
        WHERE constraint_name = 'required_qualifiers'
        AND constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'
        AND NOT EXISTS (
            SELECT 1
            FROM constraint_instances_2023 AS da
            WHERE da.property = dr.property
            AND da.constraint_name = 'required_qualifiers'
            AND da.constraint_object_parameters = dr.constraint_object_parameters
        );
        """  
        cursor.execute(consulta_req_qualifier)
        resultados_req_qualifier = cursor.fetchall()
        reqQualifier = {}
        for resultado in resultados_req_qualifier:
            propriedade = resultado[0]
            objeto = resultado[1] 
            if propriedade in reqQualifier:
                reqQualifier[propriedade].append(objeto)
            else:
                reqQualifier[propriedade] = [objeto]

    # ESPECIFICA CONFLICTS_WITH (onlyReqProp)
    if(constraint == 'conflicts_with' and only == 'True'):

        consulta_conflicts_with = """
            SELECT property, constraint_object_parameters 
            FROM dados_removidos AS dr
            WHERE constraint_name = 'conflicts_with'
            AND constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'
            AND constraint_instance NOT IN (
                SELECT constraint_instance
                FROM dados_removidos
                WHERE constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2305'
            )
            AND NOT EXISTS (
                SELECT 1
                FROM constraint_instances_2023 AS da
                WHERE da.property = dr.property
                AND da.constraint_name = 'conflicts_with'
                AND da.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'
                AND da.constraint_object_parameters = dr.constraint_object_parameters
                    );
                """

        cursor.execute(consulta_conflicts_with)
        resultados_conflicts_with_only_prop = cursor.fetchall()
        conflicts_with_only_prop = {}
        for resultado in resultados_conflicts_with_only_prop:
            propriedade = resultado[0]
            objeto = resultado[1] 
            if propriedade in conflicts_with_only_prop:
                conflicts_with_only_prop[propriedade].append(objeto)
            else:
                conflicts_with_only_prop[propriedade] = [objeto]

    # ESPECIFICA CONFLICTS_WITH (ReqPropVal)
    if(constraint == 'conflicts_with' and only == 'False'):

        consulta_conflicts_with = """
            SELECT 
                dr.constraint_instance,
                dr.property,
                p2306.constraint_object_parameters AS object_p2306,
                p2305.constraint_object_parameters AS object_p2305
            FROM 
                dados_removidos AS dr
            JOIN 
                dados_removidos p2305 
                ON dr.constraint_instance = p2305.constraint_instance 
                AND p2305.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2305'
            JOIN 
                constraint_instances_2019 p2306 
                ON dr.constraint_instance = p2306.constraint_instance 
                AND p2306.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'
            WHERE 
                dr.constraint_name = 'conflicts_with'
                AND dr.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2305'
                AND NOT EXISTS (
                    SELECT 1
                    FROM constraint_instances_2023 AS da
                    WHERE da.property = dr.property
                    AND da.constraint_name = 'conflicts_with'
                    AND da.constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2305'
                    AND da.constraint_object_parameters = dr.constraint_object_parameters
                );

        """

        cursor.execute(consulta_conflicts_with)
        resultados_conflicts_with_req_prop_val = cursor.fetchall()
        
        conflicts_with_req_prop_val = {}

        for resultado in resultados_conflicts_with_req_prop_val:
            prop = resultado[1]
            objeto_p2306 = resultado[2]
            objeto_p2305 = resultado[3]
        
            if prop not in conflicts_with_req_prop_val:
                conflicts_with_req_prop_val[prop] = [(objeto_p2306, objeto_p2305)]
            else:
                if (objeto_p2306, objeto_p2305) not in conflicts_with_req_prop_val[prop]:
                    conflicts_with_req_prop_val[prop].append((objeto_p2306, objeto_p2305))

    # ESPECIFICA single value
    if(constraint == 'single_value'):
        consulta_single_value = """
        SELECT property
        FROM dados_adicionados 
        WHERE constraint_name = 'single_value' 
        AND constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P4155'
        AND EXISTS (
            SELECT 1 
            FROM constraint_instances_2023 
            WHERE constraint_name = 'single_value' 
            AND constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P4155'
            AND property = dados_adicionados.property
        );
        """
        cursor.execute(consulta_single_value)
        resultados_single_value = cursor.fetchall()
        singleValue = []
        for resultado in resultados_single_value:
            propriedade = resultado[0]
            if propriedade not in singleValue:
                singleValue.append(propriedade)

    # ESPECIFICA IRS (onlyReqProp)
    if(only == True):
        cursor.execute("SELECT property, constraint_object_parameters FROM dados_adicionados WHERE constraint_name = ? AND constraint_predicate_parameters = 'http://www.wikidata.org/prop/qualifier/P2306'", (constraint,))
        resultados_irs_only_prop = cursor.fetchall()
        irs_only_prop = {}
        for resultado in resultados_irs_only_prop:
            propriedade = resultado[0]
            objeto = resultado[1] 
            if propriedade in irs_only_prop:
                irs_only_prop[propriedade].append(objeto)
            else:
                irs_only_prop[propriedade] = [objeto]
    
    with open(arquivo_diff, 'r', encoding="utf-8") as arq:
        leitor = csv.reader(arq)
        for linha in leitor:
            if len(linha) == 4:
                correcao = ['False', 'False', 'False', linha[0], linha[1], linha[2], linha[3]] 
                if(constraint == 'allowed_qualifiers' or constraint == 'required_qualifiers' or constraint == 'conflicts_with'):
                    correcao = ['False', 'False', 'False', 'False', linha[0], linha[1], linha[2], linha[3]] 
            else:
                if(constraint == 'one_of' or constraint == 'none_of' or constraint == 'item_requires_statement' or constraint == 'conflicts_with'):
                    correcao = ['False', 'False', 'False', 'False', linha[0], linha[1], linha[2]]  
                elif(constraint == 'single_value'):
                    correcao = ['False', 'False', 'False', linha[0], linha[1], linha[2], linha[3], linha[4]]  

                else:
                    correcao = ['False', 'False', 'False', linha[0], linha[1], linha[2]]  
                 
            # Normalizar URL da linha
            propriedade_linha = normalizar_url(linha[1])
            objeto_linha = normalizar_url(linha[2])

            # CONSTRAINT DELETADA
            # Caso onde tem mais de uma restrição com a mesma propriedade
            if(constraint == 'conflicts_with'):
                if(only == 'False'):
                    valor = normalizar_url(linha[3])
                propriedadeReq = normalizar_url(linha[2])
                
                if propriedade_linha in aux and aux[propriedade_linha] >= 1:
                    if propriedade_linha in hashmap_sem_valor_deletados and propriedadeReq in hashmap_sem_valor_deletados[propriedade_linha]:
                        correcao[0] = 'True'
                    elif only == 'False':
                        if(propriedade_linha in hashmap_com_valor_deletados and ((propriedadeReq, valor) in hashmap_com_valor_deletados[propriedade_linha])):
                            correcao[0] = 'True'
                else:
                    if propriedade_linha in propriedades_deletados:
                        correcao[0] = 'True'
            else:            
                for resultado in resultados_deletados:
                    predicado = resultado[3]
                    objeto = resultado[4]
                    propriedade = resultado[1]

                    # PARA AS CONSTRAINTS: ONE_OF E NONE_OF
                    if (constraint == 'none_of' or constraint == 'one_of'):
                        if (propriedade in aux and aux[propriedade] >= 1):
                            if (predicado == 'http://www.wikidata.org/prop/qualifier/P2305'):
                                if (propriedade == propriedade_linha and objeto == objeto_linha):
                                    correcao[0] = 'True'
                        else:
                            if (propriedade == propriedade_linha):
                                correcao[0] = 'True'

                    # PARA AS CONSTRAINTS INVERSE, REQUIRED_QUALIFIER E ALLOWED_QUALIFIER           
                    elif (constraint == 'inverse' or constraint == 'required_qualifiers' or constraint == 'allowed_qualifiers'):
                        if (propriedade in aux and aux[propriedade] >= 1):
                            if (predicado == 'http://www.wikidata.org/prop/qualifier/P2306'):
                                objeto_linha = normalizar_url(linha[3])
                                if (propriedade == propriedade_linha and objeto == objeto_linha):
                                    correcao[0] = 'True'
                        else:
                            if (propriedade == propriedade_linha):
                                correcao[0] = 'True'

                    # PARA A CONSTRAINT ITEM_REQUIRES_STATEMENT e CONFLICTS_WITH          
                    elif (constraint == 'item_requires_statement' or constraint == 'conflicts_with'):
                        if (propriedade in aux and aux[propriedade] >= 1):
                            if (predicado == 'http://www.wikidata.org/prop/qualifier/P2306'):
                                if (propriedade == propriedade_linha and objeto == objeto_linha):
                                    correcao[0] = 'True'
                        else:
                            if (propriedade == propriedade_linha):
                                correcao[0] = 'True'

                    # PARA O RESTANTE                   
                    else:
                        if (propriedade == propriedade_linha):
                            correcao[0] = 'True'
            
            # CONSTRAINT DEPRECIADA
            # Caso onde tem mais de uma restrição com a mesma propriedade
            if(constraint == 'conflicts_with'):
                propriedadeReq = normalizar_url(linha[2])
                if(only == 'False'):
                    valor = normalizar_url(linha[3])
                if (propriedade_linha in aux and aux[propriedade_linha] > 1):
                    if (propriedade_linha in hashmap_depreciados_sem_valor and propriedadeReq in hashmap_depreciados_sem_valor[propriedade_linha] ):
                            correcao[1] = 'True'
                    elif(propriedade_linha in hashmap_depreciados_com_valor and ((propriedadeReq, valor)in hashmap_depreciados_com_valor[propriedade_linha]) and only == 'False') :
                            correcao[1] = 'True' 
                else:
                    if (propriedade_linha in propriedades):
                        correcao[1] = 'True'
            else:    
                for resultado in resultados_depreciados:
                    propriedade = resultado[1]
                    predicado = resultado[3]
                    objeto = resultado[4]
                    
                    # PARA A CONSTRAINT ONE_OF E NONE_OF
                    if (constraint == 'none_of' or constraint == 'one_of'):
                        if (propriedade in aux and aux[propriedade] > 1):
                            if (predicado == 'http://www.wikidata.org/prop/qualifier/P2305'):
                                if (propriedade == propriedade_linha and objeto == objeto_linha):
                                    correcao[1] = 'True'
                        else:
                            if (propriedade == propriedade_linha):
                                correcao[1] = 'True'

                    # PARA A CONSTRAINT INVERSE, REQUIRED_QUALIFIER E ALLOWED_QUALIFIER   
                    elif (constraint == 'inverse' or constraint == 'required_qualifiers' or constraint == 'allowed_qualifiers'):
                        if (propriedade in aux and aux[propriedade] > 1):
                            if (predicado == 'http://www.wikidata.org/prop/qualifier/P2306'):
                                objeto_linha = normalizar_url(linha[3])
                                if (propriedade == propriedade_linha and objeto == objeto_linha):
                                    correcao[1] = 'True'
                        else:
                            if (propriedade == propriedade_linha):
                                correcao[1] = 'True'

                    # PARA A CONSTRAINT ITEM_REQUIRES_STATEMENT e CONFLICTS_WITH
                    elif (constraint == 'item_requires_statement' or constraint == 'conflicts_with'):
                        if (propriedade in aux and aux[propriedade] > 1):
                            if (predicado == 'http://www.wikidata.org/prop/qualifier/P2306'):
                                if (propriedade == propriedade_linha and objeto == objeto_linha):
                                    correcao[1] = 'True'
                        else:
                            if (propriedade == propriedade_linha):
                                correcao[1] = 'True'

                    # PARA O RESTANTE
                    else:
                        if (propriedade == propriedade_linha):
                            correcao[1] = 'True'
            
            # EXCEÇÃO
            entidade = linha[0]
            if propriedade_linha in prop_obj_map and entidade in prop_obj_map[propriedade_linha]:
                correcao[2] = 'True'

            # ONE OF CONSTRAINT ESPECIFICA (ADD valor na lista de valores esperados)
            if (constraint == 'one_of'):
                if propriedade_linha in oneOf and objeto_linha in oneOf[propriedade_linha]:
                    correcao[3] = 'True'

            # NONE OF CONSTRAINT ESPECIFICA (remove valor da lista de valores proibidos)
            if (constraint == 'none_of'):
                if propriedade_linha in noneOf and objeto_linha in noneOf[propriedade_linha]:
                    correcao[3] = 'True'
            
            # IRS apenas propriedade requerida
            if (constraint == 'item_requires_statement' and only == 'true'):
                propriedade_requerida = normalizar_url(linha[2])
                if propriedade_linha in irs_only_prop and propriedade_requerida in irs_only_prop[propriedade_linha]:
                    correcao[3] = 'True'
            
            # ALLOWED_QUALIFIERS ESPECIFICA (ADD O QUALIFICADOR NA LISTA DE ESPERADOS)
            if(constraint == 'allowed_qualifiers'):
                objeto_linha = normalizar_url(linha[3])
                if propriedade_linha in allowedQualifiers and objeto_linha in allowedQualifiers[propriedade_linha]:
                    correcao[3] = 'True'

            # REQUIRED_QUALIFIER ESPECIFICA (ADD O QUALIFICADOR NA LISTA DE ESPERADOS)
            if(constraint == 'required_qualifiers'):
                objeto_linha = normalizar_url(linha[3])
                if propriedade_linha in reqQualifier and objeto_linha in reqQualifier[propriedade_linha]:
                    correcao[3] = 'True'     

            # CONFLICTS_WITH apenas propriedade proibida
            if (constraint == 'conflicts_with' and only == 'True'):
                propriedade_proibida = normalizar_url(linha[2])
                if propriedade_linha in conflicts_with_only_prop and propriedade_proibida in conflicts_with_only_prop[propriedade_linha]:
                    correcao[3] = 'True'

            # CONFLICTS_WITH propriedade e valor proibido
            if (constraint == 'conflicts_with' and only == 'False'):
                propriedadeProibida = normalizar_url(linha[2])
                valor_proibido = linha[3]
                if propriedade_linha in conflicts_with_req_prop_val and ((propriedadeProibida,valor_proibido) in conflicts_with_req_prop_val[propriedade_linha]):
                    correcao[3] = 'True'       

            adicionar_correcao(arquivo_correcoes, correcao)

testar_correcoes()
