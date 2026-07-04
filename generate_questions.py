import json
import random
import re
from pathlib import Path


AREAS = [
    "Geografia",
    "História",
    "Ciências",
    "Cultura geral",
    "Cultura pop",
    "Esportes",
    "Brasil",
    "Animais e natureza",
    "Língua portuguesa",
    "Artes e literatura",
    "Tecnologia",
    "Nutrição",
    "Odontologia",
    "Enfermagem",
    "Matemática e raciocínio",
]

QUOTAS = {area: 34 for area in AREAS}
QUOTAS["Matemática e raciocínio"] = 24

DIFFICULTIES = ["Fácil", "Média", "Avançada"]
random.seed(20260704)


def norm(text):
    return re.sub(r"\s+", " ", text.strip().lower())


class Builder:
    def __init__(self):
        self.items = []
        self.seen_questions = set()
        self.answer_counts = {}

    def difficulty_for_area(self, area):
        current = sum(1 for item in self.items if item["area"] == area)
        total = QUOTAS[area]
        easy = round(total * 0.45)
        medium = round(total * 0.40)
        if current < easy:
            return "Fácil"
        if current < easy + medium:
            return "Média"
        return "Avançada"

    def options(self, answer, wrong_pool, salt=0):
        cleaned = []
        for opt in wrong_pool:
            if opt != answer and opt not in cleaned:
                cleaned.append(opt)
        if len(cleaned) < 3:
            raise ValueError(f"Poucas alternativas para {answer}")
        start = salt % len(cleaned)
        wrongs = (cleaned[start:] + cleaned[:start])[:3]
        opts = wrongs[:]
        pos = (len(self.items) + salt) % 4
        opts.insert(pos, answer)
        return opts

    def add(self, area, question, answer, wrongs, explanation):
        if len([item for item in self.items if item["area"] == area]) >= QUOTAS[area]:
            return
        question = re.sub(r"\s+", " ", question).strip()
        key = norm(question)
        if key in self.seen_questions:
            return
        if not question.endswith("?"):
            question += "?"
        self.seen_questions.add(key)
        self.items.append(
            {
                "id": f"Q{len(self.items) + 1:04d}",
                "area": area,
                "difficulty": self.difficulty_for_area(area),
                "question": question,
                "options": self.options(answer, wrongs, len(self.items)),
                "answer": answer,
                "explanation": explanation.strip(),
            }
        )
        self.answer_counts[answer] = self.answer_counts.get(answer, 0) + 1

    def fill_from_rows(self, area, rows, templates, wrong_key, explanation_key=None):
        for row in rows:
            for template in templates:
                if len([item for item in self.items if item["area"] == area]) >= QUOTAS[area]:
                    return
                question, answer, explanation = template(row)
                wrongs = [r[wrong_key] for r in rows if r[wrong_key] != answer]
                if explanation_key and row.get(explanation_key):
                    explanation = row[explanation_key]
                self.add(area, question, answer, wrongs, explanation)

    def count(self, area):
        return sum(1 for item in self.items if item["area"] == area)


def rotate(values, n):
    values = list(values)
    return values[n:] + values[:n]


def country_ref(country):
    feminine = {
        "Itália", "França", "Argentina", "China", "Índia", "Tailândia", "Austrália",
        "Nova Zelândia", "África do Sul", "Noruega", "Suécia", "Dinamarca", "Islândia",
        "Irlanda", "Suíça", "Bélgica", "Áustria", "Polônia", "Hungria", "Colômbia",
        "República Tcheca", "Croácia", "Ucrânia", "Arábia Saudita", "Indonésia",
        "Malásia", "Etiópia", "Nigéria", "Bolívia", "Venezuela", "Espanha",
        "Alemanha", "Grécia", "Turquia", "Rússia", "Coreia do Sul",
    }
    masculine = {
        "Japão", "Egito", "Canadá", "México", "Uruguai", "Peru", "Chile",
        "Reino Unido", "Marrocos", "Quênia", "Irã", "Iraque", "Gana", "Equador",
    }
    plural = {"Estados Unidos", "Países Baixos", "Filipinas"}
    if country in feminine:
        return f"da {country}"
    if country in masculine:
        return f"do {country}"
    if country in plural:
        return f"dos {country}"
    return f"de {country}"


def clue_question(clue, n, domain=None):
    clue = clue.rstrip(".")
    variants = [
        f"Qual alternativa corresponde a esta pista: {clue}?",
        f"Qual resposta combina melhor com esta descrição: {clue}?",
        f"O que está sendo descrito nesta frase: {clue}?",
        f"A pista '{clue}' aponta para qual resposta?",
        f"Qual opção se encaixa na explicação: {clue}?",
        f"Sobre {domain or 'este tema'}, qual resposta a descrição indica: {clue}?",
    ]
    return variants[n % len(variants)]


b = Builder()


countries = [
    ("Itália", "Roma", "Europa", "formato parecido com uma bota"),
    ("França", "Paris", "Europa", "Torre Eiffel"),
    ("Japão", "Tóquio", "Ásia", "Monte Fuji"),
    ("Egito", "Cairo", "África", "pirâmides de Gizé"),
    ("Canadá", "Ottawa", "América do Norte", "folha de bordo"),
    ("México", "Cidade do México", "América do Norte", "Dia dos Mortos"),
    ("Argentina", "Buenos Aires", "América do Sul", "tango"),
    ("Chile", "Santiago", "América do Sul", "deserto do Atacama"),
    ("Uruguai", "Montevidéu", "América do Sul", "Rio da Prata"),
    ("Peru", "Lima", "América do Sul", "Machu Picchu"),
    ("Colômbia", "Bogotá", "América do Sul", "café"),
    ("Portugal", "Lisboa", "Europa", "azulejos e fado"),
    ("Espanha", "Madri", "Europa", "flamenco"),
    ("Alemanha", "Berlim", "Europa", "Portão de Brandemburgo"),
    ("Reino Unido", "Londres", "Europa", "Big Ben"),
    ("Grécia", "Atenas", "Europa", "Acrópole"),
    ("Turquia", "Ancara", "Ásia", "Capadócia"),
    ("Rússia", "Moscou", "Europa e Ásia", "Kremlin"),
    ("China", "Pequim", "Ásia", "Grande Muralha"),
    ("Coreia do Sul", "Seul", "Ásia", "K-pop"),
    ("Índia", "Nova Délhi", "Ásia", "Taj Mahal"),
    ("Tailândia", "Bangkok", "Ásia", "templos budistas"),
    ("Austrália", "Camberra", "Oceania", "cangurus"),
    ("Nova Zelândia", "Wellington", "Oceania", "kiwi"),
    ("África do Sul", "Pretória", "África", "Cabo da Boa Esperança"),
    ("Marrocos", "Rabat", "África", "medinas históricas"),
    ("Quênia", "Nairóbi", "África", "safáris"),
    ("Estados Unidos", "Washington, D.C.", "América do Norte", "Estátua da Liberdade"),
    ("Cuba", "Havana", "América Central", "carros antigos coloridos"),
    ("Noruega", "Oslo", "Europa", "fiordes"),
    ("Suécia", "Estocolmo", "Europa", "prêmio Nobel"),
    ("Dinamarca", "Copenhague", "Europa", "estátua da Pequena Sereia"),
    ("Islândia", "Reykjavík", "Europa", "gêiseres"),
    ("Irlanda", "Dublin", "Europa", "trevo"),
    ("Suíça", "Berna", "Europa", "Alpes"),
    ("Países Baixos", "Amsterdã", "Europa", "moinhos e canais"),
    ("Bélgica", "Bruxelas", "Europa", "chocolates"),
    ("Áustria", "Viena", "Europa", "música clássica"),
    ("Polônia", "Varsóvia", "Europa", "Cracóvia histórica"),
    ("Hungria", "Budapeste", "Europa", "rio Danúbio"),
    ("República Tcheca", "Praga", "Europa", "ponte Carlos"),
    ("Croácia", "Zagreb", "Europa", "mar Adriático"),
    ("Ucrânia", "Kyiv", "Europa", "planícies férteis"),
    ("Arábia Saudita", "Riad", "Ásia", "Meca"),
    ("Israel", "Jerusalém", "Ásia", "Mar Morto"),
    ("Indonésia", "Jacarta", "Ásia", "ilhas vulcânicas"),
    ("Filipinas", "Manila", "Ásia", "arquipélago"),
    ("Vietnã", "Hanói", "Ásia", "baía de Ha Long"),
    ("Malásia", "Kuala Lumpur", "Ásia", "Torres Petronas"),
    ("Singapura", "Singapura", "Ásia", "cidade-estado"),
    ("Irã", "Teerã", "Ásia", "Persépolis"),
    ("Iraque", "Bagdá", "Ásia", "Mesopotâmia"),
    ("Etiópia", "Adis Abeba", "África", "café"),
    ("Nigéria", "Abuja", "África", "maior população africana"),
    ("Gana", "Acra", "África", "cacau"),
    ("Angola", "Luanda", "África", "língua portuguesa"),
    ("Moçambique", "Maputo", "África", "língua portuguesa"),
    ("Madagascar", "Antananarivo", "África", "lêmures"),
    ("Bolívia", "Sucre", "América do Sul", "salar de Uyuni"),
    ("Equador", "Quito", "América do Sul", "linha do Equador"),
    ("Venezuela", "Caracas", "América do Sul", "Salto Ángel"),
]

country_rows = [
    {"country": c, "capital": cap, "continent": cont, "known": known}
    for c, cap, cont, known in countries
]

geo_templates = [
    (lambda r: (f"Qual é a capital {country_ref(r['country'])}?", r["capital"], f"A capital {country_ref(r['country'])} é {r['capital']}.")),
    (lambda r: (f"Em qual região ou continente fica {r['country']}?", r["continent"], f"{r['country']} fica em {r['continent']}.")),
    (lambda r: (f"Qual país é muito associado a {r['known']}?", r["country"], f"{r['country']} é conhecido por {r['known']}.")),
]
for t in geo_templates:
    b.fill_from_rows("Geografia", country_rows, [t], "capital" if t == geo_templates[0] else "country")

geo_more = [
    ("Qual é o maior oceano do planeta?", "Oceano Pacífico", "O Pacífico é o maior oceano da Terra."),
    ("Qual é o menor continente em área?", "Oceania", "A Oceania é o menor continente em área."),
    ("Qual cordilheira fica na América do Sul?", "Cordilheira dos Andes", "Os Andes acompanham a parte oeste da América do Sul."),
    ("Qual deserto é conhecido como o mais seco do mundo?", "Deserto do Atacama", "O Atacama, no Chile, é famoso pela aridez extrema."),
    ("Qual rio passa pela cidade de Londres?", "Rio Tâmisa", "O Tâmisa atravessa Londres."),
    ("Qual rio é famoso por atravessar Paris?", "Rio Sena", "O Sena é um dos símbolos de Paris."),
    ("Qual canal liga o mar Mediterrâneo ao mar Vermelho?", "Canal de Suez", "O Canal de Suez fica no Egito."),
    ("Qual canal liga os oceanos Atlântico e Pacífico na América Central?", "Canal do Panamá", "O Canal do Panamá corta o istmo do Panamá."),
    ("Qual montanha é a mais alta do mundo?", "Monte Everest", "O Everest é o ponto mais alto acima do nível do mar."),
    ("Qual linha imaginária divide a Terra em hemisférios norte e sul?", "Linha do Equador", "A Linha do Equador divide a Terra ao meio."),
    ("Qual linha imaginária passa perto de Greenwich?", "Meridiano de Greenwich", "Esse meridiano é referência para longitudes e fusos horários."),
    ("Qual país tem mais ilhas no mundo?", "Suécia", "A Suécia possui centenas de milhares de ilhas catalogadas."),
    ("Qual continente abriga o Saara?", "África", "O Saara ocupa uma grande área do norte da África."),
    ("Qual mar é tão salgado que facilita a flutuação?", "Mar Morto", "O Mar Morto tem salinidade muito alta."),
    ("Qual país é uma cidade-estado no sudeste asiático?", "Singapura", "Singapura é país e cidade ao mesmo tempo."),
    ("Qual é a maior ilha do mundo?", "Groenlândia", "A Groenlândia é a maior ilha do planeta."),
    ("Qual país abriga a cidade de Machu Picchu?", "Peru", "Machu Picchu fica nos Andes peruanos."),
    ("Qual país abriga as pirâmides de Gizé?", "Egito", "As pirâmides de Gizé ficam perto do Cairo."),
    ("Qual país abriga o Taj Mahal?", "Índia", "O Taj Mahal fica na cidade de Agra."),
    ("Qual país abriga a Grande Muralha?", "China", "A Grande Muralha é um símbolo histórico da China."),
    ("Qual país é conhecido como terra do sol nascente?", "Japão", "A expressão é tradicionalmente associada ao Japão."),
    ("Qual país é conhecido por seus fiordes?", "Noruega", "A costa norueguesa é famosa pelos fiordes."),
    ("Qual capital sul-americana fica em grande altitude nos Andes?", "La Paz", "La Paz, na Bolívia, fica em altitude elevada."),
    ("Qual país tem o arquipélago de Galápagos?", "Equador", "Galápagos pertence ao Equador."),
    ("Qual país tem a ilha de Bali?", "Indonésia", "Bali é uma das ilhas da Indonésia."),
]
geo_wrong = ["Oceano Atlântico", "Europa", "Ásia", "Brasil", "Argentina", "França", "Egito", "Índia", "China", "Noruega", "Peru", "Mar Mediterrâneo", "Deserto do Saara"]
for i, (q, a, e) in enumerate(geo_more):
    b.add("Geografia", q, a, rotate(geo_wrong, i), e)


history_rows = [
    ("Quem foi conhecido como o primeiro imperador de Roma?", "Augusto", "Augusto consolidou o Império Romano."),
    ("Qual civilização construiu Machu Picchu?", "Incas", "Machu Picchu foi construída pelos incas."),
    ("Qual povo antigo construiu as pirâmides de Gizé?", "Egípcios", "As pirâmides de Gizé foram construídas no Egito Antigo."),
    ("Quem liderou a independência da Índia por meio da resistência pacífica?", "Mahatma Gandhi", "Gandhi defendia a não violência como estratégia política."),
    ("Quem foi a rainha do Egito associada a Júlio César e Marco Antônio?", "Cleópatra", "Cleópatra VII foi uma das governantes mais conhecidas do Egito."),
    ("Qual cidade italiana foi soterrada pela erupção do Vesúvio?", "Pompeia", "Pompeia foi coberta por cinzas vulcânicas em 79 d.C."),
    ("Em que país ocorreu a Revolução Francesa?", "França", "A Revolução Francesa começou em 1789."),
    ("Qual muro dividiu uma cidade alemã durante a Guerra Fria?", "Muro de Berlim", "O Muro de Berlim dividiu a cidade até 1989."),
    ("Qual guerra ficou marcada pelo uso de trincheiras na Europa?", "Primeira Guerra Mundial", "As trincheiras foram símbolo da Primeira Guerra Mundial."),
    ("Quem foi o líder britânico durante boa parte da Segunda Guerra Mundial?", "Winston Churchill", "Churchill foi primeiro-ministro do Reino Unido no período."),
    ("Qual império tinha Constantinopla como capital?", "Império Bizantino", "Constantinopla foi a capital bizantina."),
    ("Qual navegador português contornou o Cabo da Boa Esperança?", "Bartolomeu Dias", "Bartolomeu Dias chegou ao extremo sul da África."),
    ("Quem comandou a primeira viagem que deu a volta ao mundo?", "Fernão de Magalhães", "A expedição de Magalhães completou a circum-navegação."),
    ("Qual documento inglês de 1215 limitou o poder do rei?", "Magna Carta", "A Magna Carta é um marco do constitucionalismo."),
    ("Quem foi o imperador francês derrotado em Waterloo?", "Napoleão Bonaparte", "Napoleão foi derrotado em Waterloo em 1815."),
    ("Qual cidade japonesa foi atingida por uma bomba atômica em 1945 antes de Nagasaki?", "Hiroshima", "Hiroshima foi bombardeada em 6 de agosto de 1945."),
    ("Qual movimento europeu valorizou razão, ciência e crítica ao absolutismo?", "Iluminismo", "O Iluminismo influenciou revoluções modernas."),
    ("Qual período veio depois da Idade Média na Europa?", "Idade Moderna", "A Idade Moderna sucede a Idade Média na divisão tradicional."),
    ("Qual povo antigo é associado aos jogos olímpicos originais?", "Gregos", "Os Jogos Olímpicos surgiram na Grécia Antiga."),
    ("Quem foi o primeiro presidente dos Estados Unidos?", "George Washington", "Washington foi eleito após a independência dos Estados Unidos."),
    ("Qual tratado encerrou oficialmente a Primeira Guerra Mundial?", "Tratado de Versalhes", "O Tratado de Versalhes foi assinado em 1919."),
    ("Qual civilização criou uma escrita chamada cuneiforme?", "Sumérios", "A escrita cuneiforme surgiu na Mesopotâmia."),
    ("Qual cidade era o centro da democracia ateniense?", "Atenas", "Atenas é lembrada pela experiência democrática antiga."),
    ("Qual rainha inglesa dá nome à Era Vitoriana?", "Rainha Vitória", "A Era Vitoriana corresponde ao reinado de Vitória."),
    ("Qual movimento cultural europeu marcou os séculos XIV a XVI?", "Renascimento", "O Renascimento valorizou artes, ciência e humanismo."),
    ("Quem pintou a Mona Lisa?", "Leonardo da Vinci", "Leonardo da Vinci é o autor da Mona Lisa."),
    ("Qual navegação portuguesa chegou ao Brasil em 1500?", "Expedição de Pedro Álvares Cabral", "Cabral chegou ao território brasileiro em 1500."),
    ("Qual princesa assinou a Lei Áurea?", "Princesa Isabel", "A Lei Áurea foi assinada em 1888."),
    ("Qual revolta mineira teve Tiradentes como figura mais lembrada?", "Inconfidência Mineira", "Tiradentes é o nome mais associado à Inconfidência."),
    ("Qual era o nome do primeiro imperador do Brasil?", "Dom Pedro I", "Dom Pedro I proclamou a independência e tornou-se imperador."),
    ("Qual cidade foi capital do Brasil antes de Brasília?", "Rio de Janeiro", "O Rio de Janeiro foi capital federal até 1960."),
    ("Qual conflito brasileiro envolveu Brasil, Argentina e Uruguai contra o Paraguai?", "Guerra do Paraguai", "A Guerra do Paraguai ocorreu no século XIX."),
    ("Qual movimento de 1930 levou Getúlio Vargas ao poder?", "Revolução de 1930", "A Revolução de 1930 encerrou a República Velha."),
    ("Qual país foi invadido em 1939, iniciando a Segunda Guerra Mundial?", "Polônia", "A invasão da Polônia marcou o início do conflito na Europa."),
    ("Quem foi Nelson Mandela?", "Líder contra o apartheid", "Mandela lutou contra o apartheid e presidiu a África do Sul."),
    ("Qual povo fundou a cidade de Tenochtitlán?", "Astecas", "Tenochtitlán era a capital asteca."),
    ("Qual navegante é associado à chegada europeia à América em 1492?", "Cristóvão Colombo", "Colombo chegou ao Caribe em 1492."),
    ("Qual peste devastou a Europa no século XIV?", "Peste Negra", "A Peste Negra causou enorme mortalidade na Europa medieval."),
    ("Qual invenção de Gutenberg impulsionou a circulação de livros?", "Prensa de tipos móveis", "A prensa tornou a impressão mais rápida e barata."),
    ("Qual país sediou a Revolução Industrial inicialmente?", "Inglaterra", "A Revolução Industrial começou na Inglaterra."),
    ("Quem foi Joana d'Arc?", "Heroína francesa", "Joana d'Arc liderou tropas francesas na Guerra dos Cem Anos."),
]
history_wrongs = [a for _, a, _ in history_rows] + ["Império Romano", "Idade Média", "Revolução Russa", "Canudos", "Abolição"]
for i in range(260):
    q, a, e = history_rows[i % len(history_rows)]
    if i < len(history_rows):
        b.add("História", q, a, rotate(history_wrongs, i), e)
    else:
        base = history_rows[i % len(history_rows)]
        b.add("História", clue_question(base[2], i // len(history_rows), "história"), base[1], rotate(history_wrongs, i), base[2])


science_rows = [
    ("Qual é o maior planeta do Sistema Solar?", "Júpiter", "Júpiter é o maior planeta do Sistema Solar."),
    ("Qual planeta é conhecido como planeta vermelho?", "Marte", "Marte recebe esse apelido pela coloração avermelhada."),
    ("Qual gás é essencial para a respiração humana?", "Oxigênio", "O oxigênio participa da respiração celular."),
    ("Qual órgão bombeia o sangue pelo corpo?", "Coração", "O coração funciona como uma bomba muscular."),
    ("Qual é a substância natural mais dura encontrada na Terra?", "Diamante", "O diamante é formado por carbono em estrutura muito resistente."),
    ("Qual é a fórmula química da água?", "H2O", "A água é formada por hidrogênio e oxigênio."),
    ("Qual estrela fica no centro do Sistema Solar?", "Sol", "O Sol é a estrela central do nosso sistema."),
    ("Qual sentido humano usa a retina?", "Visão", "A retina fica no olho e capta luz."),
    ("Qual parte da planta realiza fotossíntese com mais frequência?", "Folha", "As folhas concentram clorofila e captam luz."),
    ("Qual metal líquido é conhecido pelo símbolo Hg?", "Mercúrio", "Hg é o símbolo químico do mercúrio."),
    ("Qual unidade mede a intensidade de corrente elétrica?", "Ampere", "Ampere é a unidade de corrente elétrica."),
    ("Qual força mantém os planetas em órbita ao redor do Sol?", "Gravidade", "A gravidade atrai corpos com massa."),
    ("Qual é o nome do processo em que a água vira vapor?", "Evaporação", "A evaporação transforma líquido em vapor."),
    ("Qual é o nome do processo em que o vapor vira líquido?", "Condensação", "A condensação transforma vapor em líquido."),
    ("Qual tecido do corpo humano conduz impulsos nervosos?", "Tecido nervoso", "O tecido nervoso transmite sinais pelo corpo."),
    ("Qual vitamina é produzida na pele com ajuda da luz solar?", "Vitamina D", "A luz solar ajuda a pele a produzir vitamina D."),
    ("Qual instrumento mede temperatura?", "Termômetro", "O termômetro mede temperatura."),
    ("Qual instrumento é usado para observar objetos muito pequenos?", "Microscópio", "O microscópio amplia estruturas pequenas."),
    ("Qual instrumento é usado para observar astros distantes?", "Telescópio", "O telescópio ajuda a observar corpos celestes."),
    ("Qual camada de gás envolve a Terra?", "Atmosfera", "A atmosfera envolve o planeta."),
    ("Qual tipo sanguíneo é conhecido como doador universal de hemácias?", "O negativo", "O tipo O negativo pode doar hemácias para muitos receptores."),
    ("Qual órgão filtra o sangue e produz urina?", "Rim", "Os rins filtram o sangue."),
    ("Qual osso protege o cérebro?", "Crânio", "O crânio envolve e protege o cérebro."),
    ("Qual músculo é associado à respiração?", "Diafragma", "O diafragma participa da inspiração e expiração."),
    ("Qual é a unidade básica dos seres vivos?", "Célula", "A célula é a menor unidade viva."),
    ("Qual molécula carrega a informação genética?", "DNA", "O DNA armazena informações hereditárias."),
    ("Qual partícula tem carga negativa?", "Elétron", "O elétron possui carga elétrica negativa."),
    ("Qual escala é usada para medir acidez?", "pH", "O pH indica acidez ou basicidade."),
    ("Qual fenômeno causa o som do trovão?", "Expansão rápida do ar", "O raio aquece o ar, que se expande rapidamente."),
    ("Qual planeta possui anéis muito visíveis?", "Saturno", "Saturno é famoso por seus anéis."),
    ("Qual camada da Terra fica no centro do planeta?", "Núcleo", "O núcleo é a parte mais interna da Terra."),
    ("Qual mudança de estado transforma sólido em líquido?", "Fusão", "Fusão é a passagem do sólido para o líquido."),
    ("Qual mudança de estado transforma líquido em sólido?", "Solidificação", "Solidificação é a passagem do líquido para o sólido."),
    ("Qual tipo de energia está associada ao movimento?", "Energia cinética", "Energia cinética depende do movimento."),
    ("Qual cientista formulou a teoria da relatividade?", "Albert Einstein", "Einstein é conhecido pela teoria da relatividade."),
    ("Qual cientista estudou a gravidade após observar a queda de uma maçã, segundo a história popular?", "Isaac Newton", "Newton formulou leis importantes da mecânica e da gravitação."),
    ("Qual planeta é o mais próximo do Sol?", "Mercúrio", "Mercúrio orbita mais perto do Sol."),
    ("Qual planeta é o mais distante entre os oito planetas?", "Netuno", "Netuno é o planeta mais distante do Sol na classificação atual."),
    ("Qual parte do ouvido ajuda no equilíbrio?", "Ouvido interno", "O ouvido interno participa do equilíbrio."),
    ("Qual gás as plantas absorvem na fotossíntese?", "Gás carbônico", "As plantas usam gás carbônico e liberam oxigênio."),
    ("Qual substância dá cor verde a muitas plantas?", "Clorofila", "A clorofila absorve luz para a fotossíntese."),
]
science_wrongs = [a for _, a, _ in science_rows] + ["Nitrogênio", "Cálcio", "Próton", "Neurônio", "Bactéria", "Carbono"]
for i in range(260):
    q, a, e = science_rows[i % len(science_rows)]
    if i < len(science_rows):
        b.add("Ciências", q, a, rotate(science_wrongs, i), e)
    else:
        b.add("Ciências", clue_question(e, i // len(science_rows), "ciências"), a, rotate(science_wrongs, i), e)


general_rows = [
    ("Qual é o único alimento conhecido por praticamente não estragar?", "Mel", "O mel tem baixa umidade e alta concentração de açúcares."),
    ("Qual objeto é usado para indicar os pontos cardeais?", "Bússola", "A bússola aponta para o norte magnético."),
    ("Qual é o nome do prêmio entregue pela Academia de Cinema dos Estados Unidos?", "Oscar", "O Oscar é uma das premiações mais conhecidas do cinema."),
    ("Qual bebida é tradicionalmente feita com folhas da erva-mate?", "Chimarrão", "O chimarrão usa erva-mate e água quente."),
    ("Qual fruta é conhecida por ter sementes do lado de fora?", "Morango", "O morango tem pequenos aquênios na superfície."),
    ("Qual peça de roupa é usada no pescoço em ocasiões formais?", "Gravata", "A gravata costuma compor trajes sociais."),
    ("Qual objeto mede o tempo em uma parede ou pulso?", "Relógio", "Relógios indicam horas, minutos e segundos."),
    ("Qual brinquedo clássico sobe com o vento preso por uma linha?", "Pipa", "A pipa voa com o vento e é controlada por linha."),
    ("Qual material é produzido pelas abelhas?", "Cera", "Abelhas produzem cera para construir favos."),
    ("Qual é o idioma mais falado no Brasil?", "Português", "O português é a língua oficial do Brasil."),
    ("Qual sinal de trânsito manda parar?", "Vermelho", "No semáforo, vermelho indica parada."),
    ("Qual alimento é base tradicional do sushi?", "Arroz", "O arroz temperado é base do sushi."),
    ("Qual instrumento corta papel com duas lâminas?", "Tesoura", "A tesoura corta por ação de duas lâminas."),
    ("Qual objeto abre fechaduras comuns?", "Chave", "A chave aciona a fechadura."),
    ("Qual é o nome da refeição feita ao acordar?", "Café da manhã", "É a primeira refeição do dia."),
    ("Qual cor resulta da mistura de azul com amarelo?", "Verde", "Azul e amarelo formam verde em mistura comum de tintas."),
    ("Qual mês tem o Dia das Crianças no Brasil?", "Outubro", "No Brasil, a data é comemorada em 12 de outubro."),
    ("Qual documento identifica oficialmente uma pessoa no Brasil?", "RG", "O RG é um documento de identificação civil."),
    ("Qual objeto é usado para proteger da chuva?", "Guarda-chuva", "O guarda-chuva ajuda a evitar que a pessoa se molhe."),
    ("Qual lugar guarda livros para consulta pública?", "Biblioteca", "Bibliotecas reúnem livros e materiais de leitura."),
    ("Qual profissão pilota aviões?", "Piloto", "Pilotos conduzem aeronaves."),
    ("Qual profissional prepara pães em uma padaria?", "Padeiro", "Padeiros produzem pães e massas."),
    ("Qual ferramenta é usada para apertar parafusos?", "Chave de fenda", "A chave de fenda encaixa em parafusos com fenda."),
    ("Qual objeto amplia letras pequenas?", "Lupa", "A lupa usa lente de aumento."),
    ("Qual transporte anda sobre trilhos?", "Trem", "Trens se deslocam por trilhos."),
    ("Qual objeto guarda dinheiro em papel ou cartões no bolso?", "Carteira", "A carteira organiza dinheiro e documentos."),
    ("Qual é o nome da pessoa que nasce na mesma data que outra?", "Aniversariante do mesmo dia", "Duas pessoas podem compartilhar o mesmo aniversário."),
    ("Qual aparelho mantém alimentos refrigerados em casa?", "Geladeira", "A geladeira conserva alimentos em baixa temperatura."),
    ("Qual objeto é usado para escrever em quadro branco?", "Caneta para quadro branco", "Esse tipo de caneta apaga com facilidade no quadro."),
    ("Qual item é usado para escovar o cabelo?", "Escova", "A escova ajuda a pentear e desembaraçar o cabelo."),
    ("Qual é o nome do local onde aviões pousam e decolam?", "Aeroporto", "Aeroportos têm pistas para pousos e decolagens."),
    ("Qual símbolo costuma representar uma ideia?", "Lâmpada", "A lâmpada virou símbolo visual de ideia."),
    ("Qual objeto é usado para marcar páginas de um livro?", "Marcador de página", "Ele marca onde a leitura parou."),
    ("Qual doce brasileiro é feito com leite condensado e chocolate?", "Brigadeiro", "O brigadeiro é comum em festas brasileiras."),
    ("Qual utensílio serve sopa?", "Concha", "A concha ajuda a servir líquidos."),
    ("Qual objeto mostra o caminho em viagens?", "Mapa", "Mapas representam lugares e rotas."),
    ("Qual aparelho toca estações de áudio por frequência?", "Rádio", "O rádio recebe transmissões sonoras."),
    ("Qual palavra se usa para agradecer em português?", "Obrigado", "Obrigado é uma forma comum de agradecimento."),
    ("Qual comemoração usa velas sobre bolo?", "Aniversário", "Velas no bolo são tradição de aniversário."),
    ("Qual item protege a cabeça ao andar de moto?", "Capacete", "O capacete reduz o risco de lesões."),
    ("Qual objeto é usado para medir peso corporal?", "Balança", "A balança informa massa ou peso em uso cotidiano."),
]
general_wrongs = [a for _, a, _ in general_rows] + ["Agenda", "Caneca", "Martelo", "Calendário", "Telefone"]
for i in range(260):
    q, a, e = general_rows[i % len(general_rows)]
    if i < len(general_rows):
        b.add("Cultura geral", q, a, rotate(general_wrongs, i), e)
    else:
        b.add("Cultura geral", clue_question(e, i // len(general_rows), "cultura geral"), a, rotate(general_wrongs, i), e)


pop_rows = [
    ("Qual é o nome do bicho de estimação do Bob Esponja?", "Gary", "Gary é o caracol de estimação do Bob Esponja."),
    ("Qual bruxo tem uma cicatriz em forma de raio?", "Harry Potter", "Harry Potter é conhecido pela cicatriz na testa."),
    ("Qual herói da Marvel usa um escudo redondo?", "Capitão América", "O escudo é a marca registrada do Capitão América."),
    ("Qual personagem da DC é conhecido como Homem-Morcego?", "Batman", "Batman atua em Gotham City."),
    ("Qual filme tem um boneco cowboy chamado Woody?", "Toy Story", "Woody é um dos personagens principais de Toy Story."),
    ("Qual desenho tem a família Simpson?", "Os Simpsons", "A família Simpson vive em Springfield."),
    ("Qual personagem azul corre em alta velocidade nos videogames?", "Sonic", "Sonic é conhecido pela velocidade."),
    ("Qual encanador de videogame usa boné vermelho com a letra M?", "Mario", "Mario é um personagem clássico da Nintendo."),
    ("Qual franquia tem sabres de luz?", "Star Wars", "Sabres de luz são armas marcantes da saga."),
    ("Qual série tem dragões e a família Targaryen?", "Game of Thrones", "A casa Targaryen é ligada aos dragões."),
    ("Qual cantora ficou conhecida como Rainha do Pop?", "Madonna", "Madonna é frequentemente chamada de Rainha do Pop."),
    ("Qual cantor é chamado de Rei do Pop?", "Michael Jackson", "Michael Jackson recebeu esse apelido popular."),
    ("Qual banda lançou a canção Bohemian Rhapsody?", "Queen", "Bohemian Rhapsody é uma das músicas mais famosas do Queen."),
    ("Qual personagem de desenho vive dizendo que viu um gatinho?", "Piu-Piu", "Piu-Piu é perseguido pelo Frajola."),
    ("Qual personagem ama lasanha e odeia segunda-feira?", "Garfield", "Garfield é conhecido por essas duas marcas."),
    ("Qual filme tem o personagem Jack Sparrow?", "Piratas do Caribe", "Jack Sparrow é o pirata da franquia."),
    ("Qual princesa da Disney perde um sapatinho de cristal?", "Cinderela", "O sapatinho de cristal é parte central da história."),
    ("Qual princesa da Disney vive no fundo do mar?", "Ariel", "Ariel é a Pequena Sereia."),
    ("Qual desenho tem um rato chamado Mickey?", "Mickey Mouse", "Mickey é um personagem clássico da Disney."),
    ("Qual personagem amarelo dos videogames come pontos em labirintos?", "Pac-Man", "Pac-Man come pontos enquanto foge dos fantasmas."),
    ("Qual jogo de blocos usa peças chamadas tetriminos?", "Tetris", "Tetris é baseado em encaixar blocos."),
    ("Qual série popular tem o grupo de amigos de Central Perk?", "Friends", "Central Perk é o café frequentado pelo grupo."),
    ("Qual filme animado tem um peixe chamado Nemo?", "Procurando Nemo", "Nemo é o peixe-palhaço da animação."),
    ("Qual personagem da Turma da Mônica troca o R pelo L?", "Cebolinha", "Cebolinha é conhecido por essa troca na fala."),
    ("Qual personagem da Turma da Mônica é forte e dona do Sansão?", "Mônica", "Mônica carrega o coelho Sansão."),
    ("Qual personagem usa um anel para se transformar em herói no desenho brasileiro?", "Capitão Planeta", "O desenho usa anéis ligados aos elementos."),
    ("Qual saga tem a escola Hogwarts?", "Harry Potter", "Hogwarts é a escola de magia da saga."),
    ("Qual filme tem um leão chamado Simba?", "O Rei Leão", "Simba é o protagonista da animação."),
    ("Qual personagem verde diz que ogros são como cebolas?", "Shrek", "Shrek faz essa comparação no filme."),
    ("Qual reality show confina participantes em uma casa vigiada por câmeras?", "Big Brother", "Big Brother acompanha participantes confinados."),
    ("Qual boneca famosa tem um namorado chamado Ken?", "Barbie", "Ken é associado à Barbie."),
    ("Qual personagem usa uma máscara e mora no pântano em uma animação de ogro?", "Shrek", "Shrek vive em um pântano."),
    ("Qual super-herói é picado por uma aranha radioativa em sua origem clássica?", "Homem-Aranha", "A origem clássica envolve uma picada de aranha."),
    ("Qual banda britânica tinha John, Paul, George e Ringo?", "The Beatles", "Os quatro formavam os Beatles."),
    ("Qual cantora brasileira é conhecida como Rainha dos Baixinhos?", "Xuxa", "Xuxa recebeu esse apelido na televisão brasileira."),
    ("Qual apresentador ficou conhecido pelo bordão 'Quem quer dinheiro'?", "Silvio Santos", "O bordão marcou programas de Silvio Santos."),
    ("Qual desenho japonês tem as esferas do dragão?", "Dragon Ball", "As esferas do dragão dão nome à série."),
    ("Qual anime tem o ninja Naruto Uzumaki?", "Naruto", "Naruto é o protagonista da série."),
    ("Qual personagem usa uma armadura vermelha e dourada?", "Homem de Ferro", "A armadura é característica do Homem de Ferro."),
    ("Qual filme mostra dinossauros recriados em um parque?", "Jurassic Park", "O parque de dinossauros é o centro da história."),
    ("Qual série acompanha médicos no hospital Grey Sloan?", "Grey's Anatomy", "A série se passa no ambiente hospitalar."),
]
pop_wrongs = [a for _, a, _ in pop_rows] + ["Frozen", "Moana", "Chaves", "Naruto", "Batman", "Star Trek"]
for i in range(260):
    q, a, e = pop_rows[i % len(pop_rows)]
    if i < len(pop_rows):
        b.add("Cultura pop", q, a, rotate(pop_wrongs, i), e)
    else:
        b.add("Cultura pop", clue_question(e, i // len(pop_rows), "cultura pop"), a, rotate(pop_wrongs, i), e)


sports_rows = [
    ("Em qual esporte se usa uma cesta e uma bola laranja?", "Basquete", "O basquete usa cestas elevadas e bola característica."),
    ("Em qual esporte o objetivo é marcar gols com os pés?", "Futebol", "No futebol, o gol é o principal objetivo."),
    ("Qual esporte usa uma raquete e uma peteca?", "Badminton", "Badminton é jogado com peteca."),
    ("Qual esporte usa uma rede alta e pode ter manchete e cortada?", "Vôlei", "Manchete e cortada são fundamentos do vôlei."),
    ("Qual esporte é praticado em uma piscina com nados diferentes?", "Natação", "A natação tem estilos como crawl, costas, peito e borboleta."),
    ("Qual esporte tem golpes chamados jab e direto?", "Boxe", "Jab e direto são golpes do boxe."),
    ("Qual esporte usa kimono e busca imobilizações ou projeções?", "Judô", "O judô usa kimono e técnicas de projeção."),
    ("Qual esporte usa taco, luva e bases?", "Beisebol", "Beisebol tem bases e rebatidas com taco."),
    ("Qual esporte tem touchdowns?", "Futebol americano", "Touchdown é a principal pontuação do futebol americano."),
    ("Qual esporte usa discos chamados puck?", "Hóquei no gelo", "O hóquei no gelo usa um disco rígido."),
    ("Qual prova combina natação, ciclismo e corrida?", "Triatlo", "O triatlo une três modalidades de resistência."),
    ("Qual modalidade olímpica usa barras paralelas e argolas?", "Ginástica artística", "Argolas e barras são aparelhos da ginástica artística."),
    ("Qual esporte é associado a birdie, eagle e tacadas?", "Golfe", "Esses termos pertencem ao golfe."),
    ("Qual esporte é disputado em sets e usa quadra dividida por rede?", "Tênis", "O tênis é disputado em games e sets."),
    ("Qual esporte tem o termo 'xeque-mate'?", "Xadrez", "Xeque-mate encerra uma partida de xadrez."),
    ("Qual corrida tem 42,195 km?", "Maratona", "A maratona oficial tem 42,195 km."),
    ("Qual esporte usa prancha sobre ondas?", "Surfe", "O surfe depende das ondas."),
    ("Qual esporte usa florete, espada ou sabre?", "Esgrima", "Essas são armas da esgrima esportiva."),
    ("Qual esporte tem arremesso de peso?", "Atletismo", "Arremesso de peso é prova do atletismo."),
    ("Qual esporte usa cavalo com obstáculos em pista?", "Hipismo", "O hipismo tem provas com saltos."),
    ("Qual modalidade usa arco e flecha?", "Tiro com arco", "O tiro com arco mira alvos a distância."),
    ("Qual esporte brasileiro mistura luta, música e roda?", "Capoeira", "A capoeira combina luta, dança e música."),
    ("Qual competição de futebol reúne seleções nacionais a cada quatro anos?", "Copa do Mundo", "A Copa do Mundo é disputada por seleções."),
    ("Qual cor de cartão expulsa um jogador no futebol?", "Vermelho", "O cartão vermelho indica expulsão."),
    ("Quantos jogadores cada time tem em campo no futebol tradicional?", "11", "Cada equipe inicia com 11 jogadores em campo."),
    ("Quantos pontos vale uma cesta de lance livre no basquete?", "1 ponto", "O lance livre vale um ponto."),
    ("Qual esporte tem uma posição chamada goleiro?", "Futebol", "O goleiro defende a meta."),
    ("Qual esporte tem uma posição chamada levantador?", "Vôlei", "O levantador organiza jogadas no vôlei."),
    ("Qual esporte usa capacete e bicicleta em pistas ou estradas?", "Ciclismo", "O ciclismo é praticado com bicicletas."),
    ("Qual arte marcial tem faixas coloridas para indicar graduação?", "Karatê", "O karatê usa faixas de graduação."),
    ("Qual modalidade é praticada sobre patins no gelo com coreografias?", "Patinação artística", "A patinação artística combina técnica e apresentação."),
    ("Qual esporte usa bola oval e scrum?", "Rugby", "Scrum é formação típica do rugby."),
    ("Qual esporte de mesa usa bolinhas e raquetes pequenas?", "Tênis de mesa", "Tênis de mesa também é chamado de pingue-pongue."),
    ("Qual esporte usa alvos e armas de ar comprimido ou fogo em provas controladas?", "Tiro esportivo", "O tiro esportivo é modalidade olímpica."),
    ("Qual esporte usa velas para aproveitar o vento?", "Vela", "A vela depende do vento para mover a embarcação."),
    ("Qual esporte usa a palavra tatame no local de luta?", "Judô", "O judô é praticado no tatame."),
    ("Qual esporte tem o termo 'home run'?", "Beisebol", "Home run é uma jogada importante no beisebol."),
    ("Qual esporte tem o termo 'ace' em saques?", "Tênis", "Ace é um saque sem resposta."),
    ("Qual modalidade é conhecida por provas de salto em distância e corrida?", "Atletismo", "O atletismo reúne corridas, saltos e arremessos."),
    ("Qual esporte é jogado com uma bola pesada e pinos?", "Boliche", "No boliche, a bola derruba pinos."),
    ("Qual esporte usa uma mesa verde e tacos para encaçapar bolas?", "Sinuca", "A sinuca é jogada com tacos e bolas em uma mesa."),
]
sports_wrongs = [a for _, a, _ in sports_rows] + ["Handebol", "Polo aquático", "Skate", "Curling", "Futsal"]
for i in range(260):
    q, a, e = sports_rows[i % len(sports_rows)]
    if i < len(sports_rows):
        b.add("Esportes", q, a, rotate(sports_wrongs, i), e)
    else:
        b.add("Esportes", clue_question(e, i // len(sports_rows), "esportes"), a, rotate(sports_wrongs, i), e)


states = [
    ("Acre", "Rio Branco", "Norte"),
    ("Alagoas", "Maceió", "Nordeste"),
    ("Amapá", "Macapá", "Norte"),
    ("Amazonas", "Manaus", "Norte"),
    ("Bahia", "Salvador", "Nordeste"),
    ("Ceará", "Fortaleza", "Nordeste"),
    ("Distrito Federal", "Brasília", "Centro-Oeste"),
    ("Espírito Santo", "Vitória", "Sudeste"),
    ("Goiás", "Goiânia", "Centro-Oeste"),
    ("Maranhão", "São Luís", "Nordeste"),
    ("Mato Grosso", "Cuiabá", "Centro-Oeste"),
    ("Mato Grosso do Sul", "Campo Grande", "Centro-Oeste"),
    ("Minas Gerais", "Belo Horizonte", "Sudeste"),
    ("Pará", "Belém", "Norte"),
    ("Paraíba", "João Pessoa", "Nordeste"),
    ("Paraná", "Curitiba", "Sul"),
    ("Pernambuco", "Recife", "Nordeste"),
    ("Piauí", "Teresina", "Nordeste"),
    ("Rio de Janeiro", "Rio de Janeiro", "Sudeste"),
    ("Rio Grande do Norte", "Natal", "Nordeste"),
    ("Rio Grande do Sul", "Porto Alegre", "Sul"),
    ("Rondônia", "Porto Velho", "Norte"),
    ("Roraima", "Boa Vista", "Norte"),
    ("Santa Catarina", "Florianópolis", "Sul"),
    ("São Paulo", "São Paulo", "Sudeste"),
    ("Sergipe", "Aracaju", "Nordeste"),
    ("Tocantins", "Palmas", "Norte"),
]
state_rows = [{"state": s, "capital": c, "region": r} for s, c, r in states]
for row in state_rows:
    b.add("Brasil", f"Qual é a capital de {row['state']}?", row["capital"], [r["capital"] for r in state_rows], f"A capital de {row['state']} é {row['capital']}.")
    b.add("Brasil", f"Em qual região fica {row['state']}?", row["region"], ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"], f"{row['state']} fica na região {row['region']}.")

brazil_rows = [
    ("Qual cidade foi planejada para ser a capital federal do Brasil?", "Brasília", "Brasília foi inaugurada como capital em 1960."),
    ("Qual rio é o maior em volume de água no Brasil?", "Rio Amazonas", "O Amazonas é o maior rio em volume de água."),
    ("Qual bioma brasileiro é conhecido pela maior floresta tropical do mundo?", "Amazônia", "A Amazônia abriga uma enorme floresta tropical."),
    ("Qual bioma brasileiro é uma grande savana tropical?", "Cerrado", "O Cerrado é conhecido pela vegetação de savana."),
    ("Qual bioma brasileiro fica em área alagável no Centro-Oeste?", "Pantanal", "O Pantanal é uma das maiores planícies alagáveis do mundo."),
    ("Qual festa popular brasileira é marcada por quadrilha e comidas de milho?", "Festa junina", "Festas juninas têm quadrilha, milho e bandeirinhas."),
    ("Qual ritmo musical nasceu na Bahia e ficou famoso no Carnaval?", "Axé", "O axé ganhou força no Carnaval baiano."),
    ("Qual ritmo brasileiro é associado ao Rio de Janeiro e às escolas de samba?", "Samba", "O samba é central nos desfiles de Carnaval."),
    ("Qual prato brasileiro costuma misturar feijão preto e carnes?", "Feijoada", "A feijoada é um prato tradicional brasileiro."),
    ("Qual doce brasileiro é enrolado com granulado?", "Brigadeiro", "O brigadeiro é feito com leite condensado e chocolate."),
    ("Qual esporte tem Pelé como maior nome histórico brasileiro?", "Futebol", "Pelé é um dos maiores nomes do futebol mundial."),
    ("Qual escritor brasileiro criou Bentinho e Capitu?", "Machado de Assis", "Os personagens são de Dom Casmurro."),
    ("Qual autora brasileira escreveu A Hora da Estrela?", "Clarice Lispector", "A Hora da Estrela é uma obra de Clarice Lispector."),
    ("Qual artista brasileira é famosa por Abaporu?", "Tarsila do Amaral", "Abaporu é uma pintura modernista de Tarsila."),
    ("Qual monumento carioca fica no alto do Corcovado?", "Cristo Redentor", "O Cristo Redentor fica no Corcovado."),
    ("Qual praia carioca é famosa pelo calçadão de ondas?", "Copacabana", "O calçadão de Copacabana tem desenho ondulado."),
    ("Qual estado é famoso pelo queijo minas?", "Minas Gerais", "O queijo minas é associado à culinária mineira."),
    ("Qual estado é famoso pelo acarajé?", "Bahia", "O acarajé é símbolo da culinária baiana."),
    ("Qual cidade é conhecida como capital do frevo?", "Recife", "O frevo é forte no Carnaval de Recife."),
    ("Qual cidade histórica mineira é ligada ao barroco e a Aleijadinho?", "Ouro Preto", "Ouro Preto preserva igrejas e obras barrocas."),
    ("Qual ave aparece no brasão da República Federativa do Brasil?", "Sabiá-laranjeira", "O sabiá-laranjeira é ave símbolo do Brasil."),
    ("Qual flor amarela aparece como símbolo nacional brasileiro?", "Ipê-amarelo", "O ipê-amarelo é associado à flora brasileira."),
    ("Qual moeda brasileira veio antes do real?", "Cruzeiro real", "O cruzeiro real foi a moeda imediatamente anterior ao real."),
    ("Qual plano econômico lançou o real?", "Plano Real", "O Plano Real criou a moeda atual."),
    ("Qual presidente inaugurou Brasília?", "Juscelino Kubitschek", "JK liderou a construção e inauguração de Brasília."),
    ("Qual grito simbólico é associado à Independência do Brasil?", "Independência ou Morte", "A frase é ligada ao episódio do Ipiranga."),
    ("Qual data marca a Independência do Brasil?", "7 de setembro", "A independência é comemorada em 7 de setembro."),
    ("Qual data marca a Proclamação da República?", "15 de novembro", "A República foi proclamada em 15 de novembro de 1889."),
    ("Qual língua é oficial no Brasil?", "Português", "O português é a língua oficial do país."),
    ("Qual país faz fronteira com quase todos os países sul-americanos, exceto Chile e Equador?", "Brasil", "O Brasil tem muitas fronteiras na América do Sul."),
]
brazil_wrongs = [a for _, a, _ in brazil_rows] + [c for _, c, _ in states] + ["Argentina", "Uruguai", "Chile"]
for i in range(260):
    q, a, e = brazil_rows[i % len(brazil_rows)]
    if b.count("Brasil") >= 205:
        break
    if i < len(brazil_rows):
        b.add("Brasil", q, a, rotate(brazil_wrongs, i), e)
    else:
        b.add("Brasil", clue_question(e, i // len(brazil_rows), "Brasil"), a, rotate(brazil_wrongs, i), e)


animal_rows = [
    ("Qual mamífero é conhecido por botar ovos?", "Ornitorrinco", "O ornitorrinco é um mamífero monotremado."),
    ("Qual animal é o maior mamífero do planeta?", "Baleia-azul", "A baleia-azul é o maior mamífero conhecido."),
    ("Qual ave não voa e é símbolo da Antártida?", "Pinguim", "Pinguins são aves adaptadas à vida aquática."),
    ("Qual animal terrestre é conhecido pelo pescoço longo?", "Girafa", "A girafa tem pescoço muito alongado."),
    ("Qual felino é o mais veloz em corrida curta?", "Guepardo", "O guepardo atinge altas velocidades em distâncias curtas."),
    ("Qual animal muda de cor para se camuflar?", "Camaleão", "Camaleões podem alterar a coloração da pele."),
    ("Qual inseto produz mel?", "Abelha", "Abelhas produzem mel a partir do néctar."),
    ("Qual animal constrói barragens com galhos?", "Castor", "Castores constroem barragens em rios e córregos."),
    ("Qual peixe é famoso por inflar o corpo?", "Baiacu", "O baiacu infla como defesa."),
    ("Qual réptil carrega uma carapaça nas costas?", "Tartaruga", "A carapaça protege o corpo da tartaruga."),
    ("Qual animal tem tromba?", "Elefante", "A tromba é uma adaptação marcante do elefante."),
    ("Qual animal é conhecido por ter listras pretas e brancas?", "Zebra", "As zebras têm listras únicas."),
    ("Qual ave é associada a imitar sons e fala humana?", "Papagaio", "Papagaios conseguem imitar sons."),
    ("Qual animal vive em colônias e é símbolo de organização?", "Formiga", "Formigas vivem em sociedades organizadas."),
    ("Qual animal é conhecido por carregar o filhote em uma bolsa?", "Canguru", "Cangurus têm marsúpio."),
    ("Qual animal marinho tem oito braços?", "Polvo", "Polvos têm oito braços."),
    ("Qual animal tem espinhos pelo corpo e se enrola para defesa?", "Ouriço", "O ouriço se protege com espinhos."),
    ("Qual animal é conhecido como rei da selva?", "Leão", "O leão recebe esse apelido popular."),
    ("Qual ave bota os maiores ovos atuais?", "Avestruz", "O avestruz bota ovos muito grandes."),
    ("Qual animal é símbolo do WWF?", "Panda-gigante", "O panda aparece no logotipo da organização."),
    ("Qual inseto passa por metamorfose e vira borboleta?", "Lagarta", "A lagarta é a fase larval das borboletas."),
    ("Qual anfíbio começa a vida como girino?", "Sapo", "Sapos passam por fase de girino."),
    ("Qual animal usa ecolocalização para se orientar no escuro?", "Morcego", "Morcegos emitem sons e interpretam ecos."),
    ("Qual animal é conhecido por dormir pendurado de cabeça para baixo?", "Morcego", "Morcegos costumam repousar pendurados."),
    ("Qual animal tem uma juba característica nos machos?", "Leão", "A juba é típica dos leões machos."),
    ("Qual animal é famoso por sua memória em ditados populares?", "Elefante", "A memória do elefante virou expressão popular."),
    ("Qual réptil rasteja sem pernas?", "Cobra", "Cobras se locomovem sem patas."),
    ("Qual animal é conhecido por soltar tinta na água?", "Lula", "Lulas podem liberar tinta para confundir predadores."),
    ("Qual ave é símbolo da paz?", "Pomba", "A pomba branca é símbolo comum da paz."),
    ("Qual animal é criado para produzir lã?", "Ovelha", "Ovelhas fornecem lã."),
    ("Qual animal é conhecido por seu casco e passo lento?", "Jabuti", "Jabutis são quelônios terrestres."),
    ("Qual inseto canta esfregando partes do corpo?", "Grilo", "Grilos produzem som por estridulação."),
    ("Qual animal da Amazônia é um grande peixe de água doce?", "Pirarucu", "O pirarucu é um dos maiores peixes de água doce."),
    ("Qual felino é símbolo da fauna brasileira e tem pintas?", "Onça-pintada", "A onça-pintada é o maior felino das Américas."),
    ("Qual ave brasileira é conhecida pelo bico enorme e colorido?", "Tucano", "Tucanos têm bico grande e colorido."),
    ("Qual animal é famoso por se fingir de morto?", "Gambá", "Alguns gambás usam esse comportamento de defesa."),
    ("Qual animal constrói teias?", "Aranha", "Aranhas produzem seda para teias."),
    ("Qual crustáceo anda de lado?", "Caranguejo", "Caranguejos costumam se deslocar lateralmente."),
    ("Qual animal é conhecido por viver em colmeias?", "Abelha", "Abelhas vivem em colmeias organizadas."),
    ("Qual animal marinho tem formato de estrela?", "Estrela-do-mar", "A estrela-do-mar tem braços em disposição radial."),
    ("Qual animal é conhecido por trocar de pele?", "Cobra", "Cobras fazem muda de pele."),
]
animal_wrongs = [a for _, a, _ in animal_rows] + ["Golfinho", "Jacaré", "Lobo", "Rinoceronte", "Flamingo"]
for i in range(260):
    q, a, e = animal_rows[i % len(animal_rows)]
    if i < len(animal_rows):
        b.add("Animais e natureza", q, a, rotate(animal_wrongs, i), e)
    else:
        b.add("Animais e natureza", clue_question(e, i // len(animal_rows), "animais e natureza"), a, rotate(animal_wrongs, i), e)


portuguese_rows = [
    ("Qual é o plural de pão?", "Pães", "Pão forma plural em pães."),
    ("Qual é o plural de cidadão?", "Cidadãos", "Cidadão forma plural em cidadãos."),
    ("Qual é o plural de animal?", "Animais", "Palavras terminadas em -al costumam formar plural em -ais."),
    ("Qual palavra está escrita corretamente?", "Exceção", "Exceção é escrita com x e ç."),
    ("Qual palavra está escrita corretamente?", "Privilégio", "Privilégio tem i depois do v."),
    ("Qual palavra está escrita corretamente?", "Beneficente", "Beneficente não tem a sílaba 'ci' no meio."),
    ("Qual é o antônimo de cedo?", "Tarde", "Tarde é o contrário de cedo nesse contexto."),
    ("Qual é o antônimo de claro?", "Escuro", "Escuro é o contrário de claro."),
    ("Qual é o sinônimo de alegre?", "Feliz", "Feliz pode ser sinônimo de alegre."),
    ("Qual é o sinônimo de veloz?", "Rápido", "Rápido pode ser sinônimo de veloz."),
    ("Qual classe de palavra dá nome a seres, objetos e lugares?", "Substantivo", "Substantivos nomeiam seres, coisas e lugares."),
    ("Qual classe de palavra indica ação, estado ou fenômeno?", "Verbo", "Verbos indicam ações, estados ou fenômenos."),
    ("Qual classe de palavra caracteriza um substantivo?", "Adjetivo", "Adjetivos atribuem características."),
    ("Qual sinal marca uma pergunta direta?", "Ponto de interrogação", "Perguntas diretas usam ponto de interrogação."),
    ("Qual sinal costuma indicar uma pausa curta?", "Vírgula", "A vírgula marca pausas e separações."),
    ("Qual acento aparece em 'avó'?", "Acento agudo", "Avó tem acento agudo no o."),
    ("Qual acento aparece em 'você'?", "Acento circunflexo", "Você usa acento circunflexo no e."),
    ("Qual palavra é oxítona?", "Café", "Café tem a última sílaba tônica."),
    ("Qual palavra é paroxítona?", "Mesa", "Mesa tem a penúltima sílaba tônica."),
    ("Qual palavra é proparoxítona?", "Médico", "Médico tem a antepenúltima sílaba tônica."),
    ("Qual é o feminino de ator?", "Atriz", "Atriz é o feminino de ator."),
    ("Qual é o masculino de abelha-rainha?", "Zangão", "Zangão é o macho das abelhas."),
    ("Qual palavra completa: Eu ___ ao mercado ontem.", "Fui", "Fui é a forma correta no passado."),
    ("Qual palavra completa: Eles ___ felizes.", "Estão", "Estão concorda com eles."),
    ("Qual palavra completa: Nós ___ estudar.", "Vamos", "Vamos concorda com nós."),
    ("Qual forma é mais adequada: ___ muitas pessoas na sala.", "Havia", "O verbo haver, no sentido de existir, fica impessoal."),
    ("Qual é a forma correta?", "Mas eu avisei", "Mas indica oposição; mais indica quantidade."),
    ("Qual é a forma correta?", "A gente vai", "A gente pede verbo no singular."),
    ("Qual palavra indica lugar?", "Onde", "Onde se refere a lugar."),
    ("Qual palavra indica motivo?", "Por que", "Por que é usado em perguntas diretas ou indiretas."),
    ("Qual palavra indica uma resposta explicativa?", "Porque", "Porque introduz explicação ou causa."),
    ("Qual é o aumentativo comum de casa?", "Casarão", "Casarão é um aumentativo de casa."),
    ("Qual é o diminutivo comum de livro?", "Livrinho", "Livrinho é diminutivo de livro."),
    ("Qual palavra tem dígrafo?", "Chave", "Ch representa um único som."),
    ("Qual palavra tem encontro consonantal?", "Prato", "Pr tem duas consoantes pronunciadas."),
    ("Qual palavra tem hiato?", "Saída", "Sa-í-da separa vogais em sílabas diferentes."),
    ("Qual palavra tem ditongo?", "Pai", "Pai tem encontro de vogais na mesma sílaba."),
    ("Qual termo substitui um nome?", "Pronome", "Pronomes substituem ou acompanham substantivos."),
    ("Qual termo liga palavras ou orações?", "Conjunção", "Conjunções fazem ligações no texto."),
    ("Qual termo indica circunstância como tempo ou modo?", "Advérbio", "Advérbios modificam verbos, adjetivos ou outros advérbios."),
    ("Qual é o coletivo de cães?", "Matilha", "Matilha é coletivo de cães."),
]
port_wrongs = [a for _, a, _ in portuguese_rows] + ["Cardume", "Plural", "Crase", "Travessão", "Interjeição"]
for i in range(260):
    q, a, e = portuguese_rows[i % len(portuguese_rows)]
    if i < len(portuguese_rows):
        b.add("Língua portuguesa", q, a, rotate(port_wrongs, i), e)
    else:
        b.add("Língua portuguesa", clue_question(e, i // len(portuguese_rows), "língua portuguesa"), a, rotate(port_wrongs, i), e)


art_rows = [
    ("De quem é a frase 'Penso, logo existo'?", "René Descartes", "A frase é associada ao filósofo René Descartes."),
    ("Quem escreveu Dom Casmurro?", "Machado de Assis", "Dom Casmurro é um romance de Machado de Assis."),
    ("Quem escreveu O Pequeno Príncipe?", "Antoine de Saint-Exupéry", "O Pequeno Príncipe foi escrito por Saint-Exupéry."),
    ("Quem pintou a Mona Lisa?", "Leonardo da Vinci", "A Mona Lisa é uma obra de Leonardo da Vinci."),
    ("Quem pintou A Noite Estrelada?", "Vincent van Gogh", "A Noite Estrelada é uma pintura de Van Gogh."),
    ("Qual artista espanhol pintou Guernica?", "Pablo Picasso", "Guernica é uma obra de Picasso."),
    ("Qual compositor ficou conhecido pela Quinta Sinfonia?", "Ludwig van Beethoven", "A Quinta Sinfonia é uma das obras mais famosas de Beethoven."),
    ("Qual compositor austríaco foi um menino prodígio da música clássica?", "Wolfgang Amadeus Mozart", "Mozart compunha desde muito jovem."),
    ("Qual escritora criou a personagem Hermione Granger?", "J. K. Rowling", "Hermione aparece na saga Harry Potter."),
    ("Quem escreveu Romeu e Julieta?", "William Shakespeare", "A tragédia é uma das peças mais conhecidas de Shakespeare."),
    ("Quem escreveu A Hora da Estrela?", "Clarice Lispector", "A obra é um romance de Clarice Lispector."),
    ("Quem escreveu Vidas Secas?", "Graciliano Ramos", "Vidas Secas retrata uma família sertaneja."),
    ("Quem escreveu Capitães da Areia?", "Jorge Amado", "Capitães da Areia é um romance de Jorge Amado."),
    ("Quem escreveu Os Lusíadas?", "Luís de Camões", "Os Lusíadas é o grande épico da literatura portuguesa."),
    ("Qual movimento artístico tem Tarsila do Amaral como grande nome no Brasil?", "Modernismo", "Tarsila é uma referência do modernismo brasileiro."),
    ("Qual pintura brasileira mostra uma figura de pés grandes ao lado de um cacto?", "Abaporu", "Abaporu foi pintado por Tarsila do Amaral."),
    ("Qual gênero literário costuma ter versos?", "Poesia", "A poesia frequentemente usa versos e ritmo."),
    ("Qual gênero teatral tem final triste ou grave?", "Tragédia", "Tragédias abordam conflitos sérios."),
    ("Qual gênero teatral busca provocar riso?", "Comédia", "Comédias têm foco no humor."),
    ("Qual arte trabalha principalmente com sons organizados no tempo?", "Música", "A música organiza sons, ritmos e silêncios."),
    ("Qual arte trabalha com movimentos corporais ritmados?", "Dança", "A dança expressa ideias pelo corpo em movimento."),
    ("Qual arte cria imagens com tinta sobre superfície?", "Pintura", "A pintura usa pigmentos em uma superfície."),
    ("Qual arte cria formas tridimensionais?", "Escultura", "Esculturas ocupam espaço em três dimensões."),
    ("Qual instrumento tem teclas brancas e pretas?", "Piano", "O piano tem teclado com teclas brancas e pretas."),
    ("Qual instrumento tem seis cordas na forma mais comum?", "Violão", "O violão comum tem seis cordas."),
    ("Qual instrumento é tocado com arco e apoiado no ombro?", "Violino", "O violino é tocado com arco."),
    ("Qual instrumento de percussão marca ritmo com baquetas?", "Bateria", "A bateria reúne tambores e pratos."),
    ("Qual museu de Paris abriga a Mona Lisa?", "Louvre", "A Mona Lisa está no Museu do Louvre."),
    ("Qual cidade italiana é famosa por canais e gôndolas?", "Veneza", "Veneza é conhecida por canais e gôndolas."),
    ("Qual artista pintou o teto da Capela Sistina?", "Michelangelo", "Michelangelo pintou afrescos na Capela Sistina."),
    ("Qual livro começa com a busca de um capitão por uma baleia branca?", "Moby Dick", "Moby Dick acompanha a obsessão do capitão Ahab."),
    ("Qual personagem literário luta contra moinhos de vento?", "Dom Quixote", "Dom Quixote confunde moinhos com gigantes."),
    ("Qual escritor criou Sherlock Holmes?", "Arthur Conan Doyle", "Sherlock Holmes foi criado por Conan Doyle."),
    ("Qual escritora brasileira escreveu Quarto de Despejo?", "Carolina Maria de Jesus", "A obra reúne diários da autora."),
    ("Qual movimento artístico usa imagens de consumo e cultura popular?", "Pop art", "A pop art usa elementos da cultura de massa."),
    ("Qual técnica japonesa dobra papel para formar figuras?", "Origami", "Origami é a arte de dobrar papel."),
    ("Qual arte japonesa organiza flores em arranjos?", "Ikebana", "Ikebana é a arte floral japonesa."),
    ("Qual artista mexicano pintou autorretratos marcantes?", "Frida Kahlo", "Frida Kahlo é famosa por seus autorretratos."),
    ("Qual artista catalão pintou relógios derretidos em A Persistência da Memória?", "Salvador Dalí", "Dalí é associado ao surrealismo."),
    ("Qual movimento artístico é ligado a Dalí e aos sonhos?", "Surrealismo", "O surrealismo explorou imagens de sonho e inconsciente."),
    ("Qual estilo musical nasceu no Rio de Janeiro com batida suave?", "Bossa nova", "A bossa nova surgiu no Brasil no fim dos anos 1950."),
]
art_wrongs = [a for _, a, _ in art_rows] + ["Realismo", "Romance", "Teatro", "Cinema", "Guitarra"]
for i in range(260):
    q, a, e = art_rows[i % len(art_rows)]
    if i < len(art_rows):
        b.add("Artes e literatura", q, a, rotate(art_wrongs, i), e)
    else:
        b.add("Artes e literatura", clue_question(e, i // len(art_rows), "artes e literatura"), a, rotate(art_wrongs, i), e)


tech_rows = [
    ("O que significa HTTPS?", "HyperText Transfer Protocol Secure", "HTTPS é a versão segura do protocolo HTTP."),
    ("Qual linguagem estrutura o conteúdo de uma página web?", "HTML", "HTML define a estrutura de páginas web."),
    ("Qual linguagem estiliza cores, fontes e layout em páginas web?", "CSS", "CSS cuida da aparência visual."),
    ("Qual linguagem costuma controlar cliques e interações no navegador?", "JavaScript", "JavaScript adiciona comportamento às páginas."),
    ("Qual componente armazena dados de forma permanente no computador?", "SSD ou HD", "SSDs e HDs armazenam arquivos mesmo sem energia."),
    ("Qual componente é conhecido como cérebro do computador?", "Processador", "O processador executa instruções."),
    ("Qual memória é temporária e usada enquanto programas estão abertos?", "RAM", "RAM é memória volátil de trabalho."),
    ("Qual item protege contas com uma camada extra além da senha?", "Autenticação em dois fatores", "Ela exige um segundo fator de verificação."),
    ("Qual ataque tenta enganar pessoas com mensagens falsas?", "Phishing", "Phishing usa fraude para roubar dados."),
    ("Qual símbolo aparece em endereços de e-mail?", "@", "O arroba separa usuário e domínio."),
    ("Qual arquivo costuma ser a página inicial de um site estático?", "index.html", "index.html é o nome padrão de entrada."),
    ("Qual formato de imagem costuma preservar transparência?", "PNG", "PNG suporta canal alfa para transparência."),
    ("Qual formato é muito usado para fotos compactadas?", "JPEG", "JPEG comprime fotografias com perda."),
    ("Qual formato é usado para documentos portáveis?", "PDF", "PDF preserva layout de documentos."),
    ("Qual serviço traduz nomes de sites em endereços IP?", "DNS", "DNS resolve domínios para IPs."),
    ("Qual rede permite conectar dispositivos próximos sem fio?", "Bluetooth", "Bluetooth conecta dispositivos em curta distância."),
    ("Qual tecnologia conecta dispositivos à internet sem fio em casa?", "Wi-Fi", "Wi-Fi usa redes sem fio locais."),
    ("Qual comando salva alterações versionadas em Git?", "commit", "O commit registra uma versão no histórico."),
    ("Qual comando envia commits locais para um repositório remoto?", "push", "Push publica commits no remoto."),
    ("Qual comando baixa alterações de um repositório remoto?", "pull", "Pull traz atualizações remotas."),
    ("Qual plataforma é muito usada para hospedar repositórios Git?", "GitHub", "GitHub hospeda repositórios e colaboração."),
    ("Qual tecnologia permite executar código em navegadores modernos?", "JavaScript", "JavaScript roda nativamente no navegador."),
    ("Qual elemento de formulário aceita uma senha sem mostrar os caracteres?", "input type='password'", "Esse tipo mascara a senha digitada."),
    ("Qual armazenamento do navegador guarda dados sem expirar automaticamente?", "localStorage", "localStorage persiste dados no navegador."),
    ("Qual API do navegador pode gerar sons sem arquivos de áudio?", "Web Audio API", "A Web Audio API cria e processa áudio no navegador."),
    ("Qual sigla representa inteligência artificial?", "IA", "IA é inteligência artificial."),
    ("Qual termo descreve programas maliciosos em geral?", "Malware", "Malware é software criado para causar dano ou abuso."),
    ("Qual cópia de segurança ajuda a recuperar arquivos perdidos?", "Backup", "Backup é uma cópia de segurança."),
    ("Qual peça exibe imagens geradas pelo computador?", "Monitor", "O monitor mostra a interface visual."),
    ("Qual periférico move o cursor na tela?", "Mouse", "O mouse controla o ponteiro."),
    ("Qual tecla costuma confirmar uma ação ou quebra de linha?", "Enter", "Enter confirma comandos em muitos contextos."),
    ("Qual tecla apaga caracteres à esquerda do cursor?", "Backspace", "Backspace remove o caractere anterior."),
    ("Qual tecla alterna letras maiúsculas fixas?", "Caps Lock", "Caps Lock trava letras maiúsculas."),
    ("Qual unidade mede armazenamento digital?", "Byte", "Bytes medem informação digital."),
    ("Qual conjunto de oito bits forma uma unidade básica de armazenamento?", "Byte", "Um byte tem oito bits."),
    ("Qual parte da URL vem depois de https:// e identifica o site?", "Domínio", "O domínio identifica o endereço do site."),
    ("Qual termo descreve interface que se adapta ao celular?", "Responsiva", "Design responsivo se ajusta ao tamanho da tela."),
    ("Qual prática melhora contraste e navegação para mais pessoas?", "Acessibilidade", "Acessibilidade torna interfaces mais utilizáveis."),
    ("Qual erro ocorre quando uma página não é encontrada?", "404", "HTTP 404 indica recurso não encontrado."),
    ("Qual código HTTP indica sucesso comum em uma requisição?", "200", "HTTP 200 indica sucesso."),
    ("Qual arquivo pode definir instruções para robôs de busca?", "robots.txt", "robots.txt orienta rastreadores."),
]
tech_wrongs = [a for _, a, _ in tech_rows] + ["XML", "Firewall", "CPU", "GPU", "Token", "Cache"]
for i in range(260):
    q, a, e = tech_rows[i % len(tech_rows)]
    if i < len(tech_rows):
        b.add("Tecnologia", q, a, rotate(tech_wrongs, i), e)
    else:
        b.add("Tecnologia", clue_question(e, i // len(tech_rows), "tecnologia"), a, rotate(tech_wrongs, i), e)


nutrition_rows = [
    ("Qual vitamina é produzida na pele com ajuda da luz solar?", "Vitamina D", "A luz solar ajuda na produção de vitamina D."),
    ("Qual mineral é muito associado à saúde dos ossos?", "Cálcio", "O cálcio participa da formação de ossos e dentes."),
    ("Qual nutriente é a principal fonte rápida de energia para o corpo?", "Carboidrato", "Carboidratos são fonte comum de energia."),
    ("Qual nutriente ajuda na construção e reparo de tecidos?", "Proteína", "Proteínas participam da formação e reparo de tecidos."),
    ("Qual tipo de gordura deve aparecer em menor quantidade nos rótulos?", "Gordura trans", "Gordura trans deve ser evitada quando possível."),
    ("Qual bebida é essencial para hidratação diária?", "Água", "A água é fundamental para o funcionamento do corpo."),
    ("Qual grupo alimentar inclui feijão, lentilha e grão-de-bico?", "Leguminosas", "Leguminosas incluem feijões, lentilhas e grão-de-bico."),
    ("Qual fruta é famosa por conter vitamina C?", "Laranja", "A laranja é lembrada pelo teor de vitamina C."),
    ("Qual alimento é conhecido por ser fonte de ômega-3?", "Sardinha", "Peixes como sardinha podem fornecer ômega-3."),
    ("Qual item do rótulo mostra energia em kcal?", "Valor energético", "Valor energético indica calorias do alimento."),
    ("Qual parte do rótulo lista ingredientes em ordem de quantidade?", "Lista de ingredientes", "Ingredientes aparecem do maior para o menor peso."),
    ("Qual expressão indica porção recomendada no rótulo?", "Porção", "A porção define a base das informações nutricionais."),
    ("Qual alimento é fonte comum de fibras?", "Aveia", "A aveia contém fibras alimentares."),
    ("Qual hábito ajuda a perceber fome e saciedade?", "Comer com atenção", "Atenção durante a refeição ajuda a perceber sinais do corpo."),
    ("Qual refeição costuma abrir o dia?", "Café da manhã", "É a primeira refeição após acordar."),
    ("Qual nutriente não fornece calorias, mas é indispensável?", "Água", "A água não fornece energia, mas é essencial."),
    ("Qual vitamina é muito associada à coagulação do sangue?", "Vitamina K", "A vitamina K participa da coagulação."),
    ("Qual mineral é parte da hemoglobina?", "Ferro", "O ferro participa do transporte de oxigênio no sangue."),
    ("Qual alimento é derivado do leite?", "Iogurte", "Iogurte é um derivado lácteo."),
    ("Qual método usa calor seco para preparar alimentos?", "Assar", "Assar usa calor seco, geralmente no forno."),
    ("Qual método usa água fervente?", "Cozinhar", "Cozinhar em água envolve fervura."),
    ("Qual sabor é percebido em alimentos como limão?", "Azedo", "Limão tem sabor ácido ou azedo."),
    ("Qual sabor é associado ao açúcar?", "Doce", "O açúcar é referência de sabor doce."),
    ("Qual alimento é uma oleaginosa?", "Castanha", "Castanhas fazem parte das oleaginosas."),
    ("Qual nutriente aparece em maior quantidade em óleos?", "Lipídios", "Óleos são ricos em gorduras ou lipídios."),
    ("Qual opção é um cereal?", "Arroz", "Arroz é um cereal amplamente consumido."),
    ("Qual opção é uma hortaliça folhosa?", "Alface", "Alface é uma folha usada em saladas."),
    ("Qual opção é uma raiz comestível?", "Cenoura", "Cenoura é uma raiz consumida como alimento."),
    ("Qual alimento é fonte vegetal comum de proteína?", "Feijão", "Feijão fornece proteína vegetal."),
    ("Qual alimento é conhecido por conter potássio?", "Banana", "Banana é lembrada pelo potássio."),
    ("Qual termo indica ausência de glúten?", "Sem glúten", "A expressão aparece em alimentos sem glúten."),
    ("Qual grão é base do pão tradicional?", "Trigo", "Farinha de trigo é base de muitos pães."),
    ("Qual produto é feito pela fermentação do leite?", "Iogurte", "Iogurte resulta da fermentação do leite."),
    ("Qual nutriente é abundante em frutas e verduras e ajuda o intestino?", "Fibra", "Fibras ajudam o funcionamento intestinal."),
    ("Qual cuidado simples reduz risco de contaminação na cozinha?", "Lavar as mãos", "Higienizar as mãos é cuidado básico de segurança."),
    ("Qual utensílio ajuda a separar alimentos crus de cozidos com segurança?", "Tábuas separadas", "Separar tábuas reduz contaminação cruzada."),
    ("Qual prática preserva alimentos em baixa temperatura?", "Refrigeração", "Refrigeração desacelera deterioração."),
    ("Qual refeição pequena pode ocorrer entre almoço e jantar?", "Lanche", "Lanche é uma refeição intermediária."),
    ("Qual profissional orienta planos alimentares individualizados no Brasil?", "Nutricionista", "Nutricionistas são habilitados para prescrição dietética."),
    ("Qual expressão descreve comer variados grupos de alimentos?", "Alimentação variada", "Variedade ajuda a incluir diferentes nutrientes."),
    ("Qual alimento é usado como base do cuscuz nordestino?", "Milho", "O cuscuz nordestino costuma usar flocos de milho."),
]
nutrition_wrongs = [a for _, a, _ in nutrition_rows] + ["Sódio", "Zinco", "Farinha", "Chá", "Queijo"]
for i in range(260):
    q, a, e = nutrition_rows[i % len(nutrition_rows)]
    if i < len(nutrition_rows):
        b.add("Nutrição", q, a, rotate(nutrition_wrongs, i), e)
    else:
        b.add("Nutrição", clue_question(e, i // len(nutrition_rows), "nutrição"), a, rotate(nutrition_wrongs, i), e)


dental_rows = [
    ("Qual é o nome popular dos terceiros molares?", "Dentes do siso", "Terceiros molares são chamados popularmente de sisos."),
    ("Qual item é usado com creme dental para limpar os dentes?", "Escova de dentes", "A escova remove resíduos e ajuda na higiene bucal."),
    ("Qual fio ajuda a limpar entre os dentes?", "Fio dental", "O fio dental alcança espaços entre os dentes."),
    ("Qual profissional cuida da saúde bucal?", "Dentista", "Dentistas atuam na prevenção e tratamento bucal."),
    ("Qual parte visível do dente fica acima da gengiva?", "Coroa", "A coroa é a parte visível do dente."),
    ("Qual parte prende o dente ao osso?", "Raiz", "A raiz fixa o dente no osso alveolar."),
    ("Qual tecido duro reveste a coroa do dente?", "Esmalte", "O esmalte é o tecido mais duro do dente."),
    ("Qual tecido fica abaixo do esmalte?", "Dentina", "A dentina fica sob o esmalte."),
    ("Qual tecido mole fica no centro do dente?", "Polpa", "A polpa contém vasos e nervos."),
    ("Qual problema é causado pela ação de bactérias e ácidos no dente?", "Cárie", "A cárie danifica os tecidos dentários."),
    ("Qual placa pegajosa se forma nos dentes?", "Biofilme dental", "Biofilme é uma camada de microrganismos."),
    ("Qual substância ajuda a fortalecer o esmalte contra cáries?", "Flúor", "O flúor ajuda na proteção do esmalte."),
    ("Qual proteção pode ser usada no dente para prevenir cárie em sulcos?", "Selante", "Selantes protegem fissuras e sulcos."),
    ("Qual exame de imagem ajuda a ver estruturas internas dos dentes?", "Radiografia", "Radiografias auxiliam a avaliação odontológica."),
    ("Qual material pode restaurar pequenas perdas dentárias?", "Resina composta", "Resina composta é usada em restaurações."),
    ("Qual especialidade alinha dentes com aparelhos?", "Ortodontia", "Ortodontia corrige posição dos dentes e mordida."),
    ("Qual aparelho pode ser usado para alinhar dentes?", "Aparelho ortodôntico", "Aparelhos movem dentes gradualmente."),
    ("Qual parte rosada envolve os dentes?", "Gengiva", "A gengiva protege e envolve os dentes."),
    ("Qual sangramento ao escovar pode indicar inflamação gengival?", "Sangramento gengival", "Sangramento pode ser sinal de gengiva inflamada."),
    ("Qual dente costuma cortar alimentos na frente da boca?", "Incisivo", "Incisivos cortam alimentos."),
    ("Qual dente pontudo ajuda a rasgar alimentos?", "Canino", "Caninos ajudam a rasgar."),
    ("Qual dente posterior ajuda a triturar alimentos?", "Molar", "Molares trituram alimentos."),
    ("Qual dente fica entre caninos e molares?", "Pré-molar", "Pré-molares ficam na região intermediária."),
    ("Quantos dentes permanentes um adulto costuma ter, incluindo sisos?", "32", "A dentição permanente completa pode ter 32 dentes."),
    ("Quantos dentes de leite uma criança costuma ter?", "20", "A dentição decídua completa tem 20 dentes."),
    ("Qual hábito diário ajuda a controlar biofilme dental?", "Escovação", "Escovar os dentes ajuda a remover biofilme."),
    ("Qual açúcar frequente na dieta favorece cáries quando a higiene é ruim?", "Sacarose", "A sacarose pode alimentar bactérias do biofilme."),
    ("Qual instrumento odontológico aspira saliva durante o atendimento?", "Sugadora", "A sugadora remove saliva e líquidos."),
    ("Qual cadeira é usada no consultório odontológico?", "Cadeira odontológica", "A cadeira posiciona o paciente no atendimento."),
    ("Qual luz auxilia a visão do dentista durante o atendimento?", "Refletor", "O refletor ilumina a boca."),
    ("Qual molde registra formato dos dentes?", "Moldagem", "A moldagem copia estruturas bucais."),
    ("Qual protetor pode ser usado por atletas para proteger dentes?", "Protetor bucal", "Protetores bucais reduzem impacto em esportes."),
    ("Qual especialidade trata gengiva e estruturas de suporte?", "Periodontia", "Periodontia cuida dos tecidos de suporte."),
    ("Qual especialidade trata canal dentário?", "Endodontia", "Endodontia é ligada ao tratamento de canal."),
    ("Qual especialidade cuida de crianças na odontologia?", "Odontopediatria", "Odontopediatria atende crianças."),
    ("Qual item não substitui a escovação, mas ajuda no hálito?", "Enxaguante bucal", "Enxaguantes podem complementar a higiene."),
    ("Qual camada mineralizada cobre a raiz?", "Cemento", "O cemento reveste a raiz dentária."),
    ("Qual articulação movimenta a mandíbula?", "ATM", "A articulação temporomandibular move a mandíbula."),
    ("Qual osso móvel forma a mandíbula inferior?", "Mandíbula", "A mandíbula é o osso móvel da face."),
    ("Qual osso sustenta os dentes superiores?", "Maxila", "A maxila abriga os dentes superiores."),
    ("Qual registro mostra a mordida entre arcadas?", "Registro de mordida", "Ele ajuda a avaliar encaixe dos dentes."),
]
dental_wrongs = [a for _, a, _ in dental_rows] + ["Cúspide", "Palato", "Língua", "Anestesia", "Espátula"]
for i in range(260):
    q, a, e = dental_rows[i % len(dental_rows)]
    if i < len(dental_rows):
        b.add("Odontologia", q, a, rotate(dental_wrongs, i), e)
    else:
        b.add("Odontologia", clue_question(e, i // len(dental_rows), "odontologia"), a, rotate(dental_wrongs, i), e)


nursing_rows = [
    ("Qual profissional costuma aferir pressão arterial em triagens de saúde?", "Enfermeiro ou técnico de enfermagem", "Profissionais de enfermagem frequentemente aferem sinais vitais."),
    ("Qual equipamento mede pressão arterial?", "Esfigmomanômetro", "O esfigmomanômetro mede pressão arterial."),
    ("Qual instrumento escuta sons cardíacos e respiratórios?", "Estetoscópio", "O estetoscópio amplifica sons do corpo."),
    ("Qual sinal vital indica batimentos por minuto?", "Pulso", "O pulso reflete a frequência cardíaca."),
    ("Qual sinal vital indica calor corporal?", "Temperatura", "Temperatura corporal é um sinal vital."),
    ("Qual equipamento mede temperatura?", "Termômetro", "Termômetros medem temperatura."),
    ("Qual equipamento mede oxigenação no dedo?", "Oxímetro", "O oxímetro estima saturação de oxigênio."),
    ("Qual sigla costuma indicar equipamento de proteção individual?", "EPI", "EPI significa equipamento de proteção individual."),
    ("Qual EPI protege as mãos?", "Luvas", "Luvas reduzem contato direto com materiais."),
    ("Qual EPI protege nariz e boca?", "Máscara", "Máscaras ajudam a proteger vias respiratórias."),
    ("Qual prática simples reduz transmissão de microrganismos?", "Higienização das mãos", "Higienizar as mãos é cuidado essencial."),
    ("Qual líquido pode ser usado para higienização das mãos quando indicado?", "Álcool 70%", "Álcool 70% é usado para antissepsia das mãos."),
    ("Qual documento registra cuidados e observações do paciente?", "Prontuário", "O prontuário reúne registros assistenciais."),
    ("Qual local costuma receber pacientes para primeira avaliação?", "Triagem", "A triagem organiza prioridades de atendimento."),
    ("Qual termo indica medicamento aplicado por injeção na veia?", "Intravenoso", "Intravenoso significa dentro da veia."),
    ("Qual termo indica aplicação no músculo?", "Intramuscular", "Intramuscular significa no músculo."),
    ("Qual termo indica aplicação sob a pele?", "Subcutâneo", "Subcutâneo significa abaixo da pele."),
    ("Qual material perfurocortante exige descarte em recipiente rígido?", "Agulha", "Agulhas devem ser descartadas em coletor apropriado."),
    ("Qual objeto identifica o paciente no punho?", "Pulseira de identificação", "A pulseira ajuda a conferir identidade."),
    ("Qual conferência evita trocar pacientes antes de procedimentos?", "Identificação correta", "Conferir identidade reduz erros."),
    ("Qual sinal indica número de respirações por minuto?", "Frequência respiratória", "Ela conta ciclos respiratórios por minuto."),
    ("Qual medida usa quilogramas no prontuário?", "Peso", "Peso costuma ser registrado em kg."),
    ("Qual medida usa centímetros ou metros?", "Altura", "Altura é medida em cm ou m."),
    ("Qual posição deixa a pessoa deitada de barriga para cima?", "Decúbito dorsal", "Decúbito dorsal é deitado com dorso para baixo."),
    ("Qual posição deixa a pessoa de lado?", "Decúbito lateral", "Decúbito lateral é deitado lateralmente."),
    ("Qual item ajuda a transportar pacientes sentados?", "Cadeira de rodas", "Cadeiras de rodas facilitam transporte."),
    ("Qual item ajuda a transportar pacientes deitados?", "Maca", "Macas transportam pacientes deitados."),
    ("Qual área do hospital prepara materiais esterilizados?", "CME", "A Central de Material e Esterilização processa materiais."),
    ("Qual técnica reduz microrganismos em materiais?", "Esterilização", "Esterilização elimina formas de vida microbiana."),
    ("Qual termo indica ausência de contaminação por microrganismos?", "Assepsia", "Assepsia busca evitar contaminação."),
    ("Qual bolsa coleta urina em alguns pacientes?", "Bolsa coletora", "A bolsa coletora armazena urina drenada."),
    ("Qual medida evita quedas em pacientes com risco?", "Orientar e sinalizar risco", "Sinalização e orientação ajudam na prevenção."),
    ("Qual sinal no leito ajuda equipes a perceber precauções especiais?", "Identificação visual", "Sinalizações orientam condutas da equipe."),
    ("Qual termo descreve limpeza de uma superfície?", "Higienização", "Higienização remove sujeira e reduz microrganismos."),
    ("Qual profissional coordena equipes de enfermagem?", "Enfermeiro", "Enfermeiros coordenam cuidados e equipes."),
    ("Qual membro da equipe executa muitos cuidados sob supervisão?", "Técnico de enfermagem", "Técnicos executam cuidados conforme atribuições."),
    ("Qual setor atende urgências e emergências?", "Pronto atendimento", "Pronto atendimento recebe casos urgentes."),
    ("Qual escala costuma avaliar dor perguntando uma nota?", "Escala numérica", "A escala numérica usa notas para dor."),
    ("Qual cuidado é essencial antes de administrar medicamento?", "Conferir os certos da medicação", "Conferências reduzem risco de erro."),
    ("Qual termo indica queda da cama ou da própria altura?", "Queda", "Queda é evento que exige prevenção e registro."),
    ("Qual recipiente recebe descarte de agulhas?", "Coletor de perfurocortantes", "O coletor rígido evita acidentes."),
]
nursing_wrongs = [a for _, a, _ in nursing_rows] + ["Bisturi", "Sonda", "Curativo", "Vacina", "Leito"]
for i in range(260):
    q, a, e = nursing_rows[i % len(nursing_rows)]
    if i < len(nursing_rows):
        b.add("Enfermagem", q, a, rotate(nursing_wrongs, i), e)
    else:
        b.add("Enfermagem", clue_question(e, i // len(nursing_rows), "enfermagem"), a, rotate(nursing_wrongs, i), e)


math_rows = [
    ("Se uma dúzia tem 12 unidades, quanto é meia dúzia?", "6", "Meia dúzia é metade de 12."),
    ("Qual número vem depois de 99?", "100", "Depois de 99 vem 100."),
    ("Qual é o dobro de 25?", "50", "Dobro significa multiplicar por 2."),
    ("Qual é a metade de 80?", "40", "Metade de 80 é 40."),
    ("Quantos lados tem um triângulo?", "3", "Triângulos têm três lados."),
    ("Quantos lados tem um quadrado?", "4", "Quadrados têm quatro lados iguais."),
    ("Quantos graus tem uma volta completa?", "360", "Uma volta completa tem 360 graus."),
    ("Quantos minutos tem uma hora?", "60", "Uma hora tem 60 minutos."),
    ("Quantos segundos tem um minuto?", "60", "Um minuto tem 60 segundos."),
    ("Quantos centímetros tem um metro?", "100", "Um metro tem 100 centímetros."),
    ("Qual número é par?", "28", "Números pares são divisíveis por 2."),
    ("Qual número é ímpar?", "35", "Números ímpares não são divisíveis por 2."),
    ("Se hoje é segunda, que dia vem depois de amanhã?", "Quarta-feira", "Depois de amanhã, a partir de segunda, é quarta."),
    ("Qual forma geométrica não tem lados?", "Círculo", "O círculo não possui lados retos."),
    ("Qual é o próximo número da sequência 2, 4, 6, 8?", "10", "A sequência aumenta de 2 em 2."),
    ("Qual é o próximo número da sequência 5, 10, 15, 20?", "25", "A sequência aumenta de 5 em 5."),
    ("Qual é o resultado de 9 + 6?", "15", "9 + 6 = 15."),
    ("Qual é o resultado de 12 - 7?", "5", "12 - 7 = 5."),
    ("Qual é o resultado de 3 × 7?", "21", "3 vezes 7 é 21."),
    ("Qual é o resultado de 48 ÷ 6?", "8", "48 dividido por 6 é 8."),
    ("Qual fração representa metade?", "1/2", "Um meio representa metade."),
    ("Qual fração representa um quarto?", "1/4", "Um quarto é uma parte de quatro iguais."),
    ("Qual número romano representa 10?", "X", "X representa 10 em algarismos romanos."),
    ("Qual número romano representa 5?", "V", "V representa 5 em algarismos romanos."),
    ("Se uma moeda é lançada, quantos resultados básicos são possíveis?", "2", "Cara ou coroa são os dois resultados básicos."),
    ("Qual é o nome do ângulo menor que 90 graus?", "Agudo", "Ângulos agudos medem menos de 90 graus."),
    ("Qual é o nome do ângulo de 90 graus?", "Reto", "Ângulo reto mede 90 graus."),
    ("Qual é o nome do ângulo maior que 90 e menor que 180 graus?", "Obtuso", "Ângulo obtuso fica entre 90 e 180 graus."),
]
math_wrongs = [a for _, a, _ in math_rows] + ["12", "24", "30", "45", "90", "180", "1/3", "Quadrado"]
for i in range(140):
    q, a, e = math_rows[i % len(math_rows)]
    if i < len(math_rows):
        b.add("Matemática e raciocínio", q, a, rotate(math_wrongs, i), e)
    else:
        b.add("Matemática e raciocínio", clue_question(e, i // len(math_rows), "matemática e raciocínio"), a, rotate(math_wrongs, i), e)


def assert_complete():
    counts = {area: b.count(area) for area in AREAS}
    missing = {area: QUOTAS[area] - count for area, count in counts.items() if count != QUOTAS[area]}
    if missing:
        raise RuntimeError(f"Categorias incompletas: {missing}")


assert_complete()

for i, item in enumerate(b.items, start=1):
    item["id"] = f"Q{i:04d}"

json_text = json.dumps(b.items, ensure_ascii=False, indent=2)
Path("questions.json").write_text(json_text + "\n", encoding="utf-8")
Path("questions.js").write_text("window.QUESTION_BANK = " + json_text + ";\n", encoding="utf-8")

print(f"Geradas {len(b.items)} perguntas.")
for area in AREAS:
    print(f"{area}: {b.count(area)}")
