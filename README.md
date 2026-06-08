# SGPA – Sistema de Gestão Pedagógica Automatizada

<p align="center">
  <img src="docs/logo-sgpa.png" width="220">
</p>

<p align="center">
  <strong>Transformando dados escolares em decisões inteligentes.</strong>
</p>

---

## Sobre o Projeto

O SGPA (Sistema de Gestão Pedagógica Automatizada) é uma plataforma desenvolvida para apoiar gestores escolares, coordenadores pedagógicos e professores no monitoramento, organização e análise de processos educacionais.

O sistema automatiza atividades que tradicionalmente demandam grande esforço operacional, transformando dados pedagógicos em informações estratégicas para a tomada de decisão.

O projeto foi idealizado e desenvolvido por **Leandro Sabino dos Santos**, professor de Física e fundador da **EduData IA**.

---

## Problema que o SGPA Resolve

As equipes gestoras frequentemente enfrentam desafios relacionados a:

- Monitoramento manual de documentos pedagógicos;
- Acompanhamento de agendas docentes;
- Controle de Guias de Aprendizagem;
- Verificação de evidências pedagógicas;
- Conformidade com premissas do Programa Ensino Integral (PEI);
- Consolidação de indicadores educacionais;
- Tomada de decisão baseada em dados.

O SGPA foi criado para automatizar esses processos.

---

## Principais Funcionalidades

### Gestão Pedagógica

- Monitoramento de Agendas Semanais;
- Controle de Guias de Aprendizagem;
- Verificação de Evidências Pedagógicas;
- Monitoramento de PDI;
- Acompanhamento de Planejamentos.

### Gestão Operacional

- Cadastro de Professores;
- Cadastro de Alunos;
- Registro de Ocorrências;
- Escala de Substituição;
- Organização automatizada de documentos.

### Analytics Educacional

- Indicadores pedagógicos;
- Relatórios gerenciais;
- Dashboards de acompanhamento;
- Monitoramento de conformidade.

### Inteligência Artificial

- Análise de perfil docente;
- Apoio à tomada de decisão;
- Recomendações pedagógicas;
- Estrutura preparada para expansão com IA Educacional.

---

## Arquitetura do Sistema

```text
Google Drive
      ↓
Drive Scanner
      ↓
Processamento de Dados
      ↓
Indicadores
      ↓
Dashboard
      ↓
Análises IA
      ↓
Tomada de Decisão
```

---

## Estrutura do Projeto

```text
SGPA/
│
├── main.py
├── drive_scanner.py
├── dashboard.py
├── alunos.py
├── analisar_perfil.py
├── config.exemplo.py
├── requirements.txt
│
├── docs/
│   ├── logo-sgpa.png
│   ├── dashboard.png
│   ├── arquitetura.png
│
└── README.md
```

---

## Tecnologias Utilizadas

- Python
- Google Drive API
- Google Sheets API
- Google OAuth
- Pandas
- HTML
- Inteligência Artificial
- Data Analytics

---

## Roadmap

### Versão Atual

- Monitoramento Pedagógico
- Dashboard Gerencial
- Cadastro de Professores
- Cadastro de Alunos
- Registro de Ocorrências
- Análise de Perfil Docente com IA

### Próximas Funcionalidades

- Radar PEI
- Perfil Docente Inteligente
- EduData Analytics
- Assistente IA Educacional
- Controle de Usuários
- Multi-escolas

### Futuro

- Plataforma SaaS
- Aplicativo Mobile
- Machine Learning Educacional
- Dashboard para Diretorias de Ensino
- Dashboard para Redes Municipais

---

## Casos de Uso

### Diretor Escolar

Acompanhar indicadores e conformidade pedagógica em tempo real.

### Coordenador Pedagógico

Monitorar agendas, evidências e documentos docentes.

### Professor

Organizar documentos e acompanhar demandas pedagógicas.

---

## EduData IA

O SGPA é um produto da **EduData IA**, iniciativa voltada ao desenvolvimento de soluções em:

- Gestão Educacional;
- Inteligência Artificial aplicada à Educação;
- Ciência de Dados Educacionais;
- Governança Pedagógica;
- Analytics Educacional.

---

## Autor

**Leandro Sabino dos Santos**

Professor de Física  
Mestre em Ensino de Física  
Fundador da EduData IA

---

## Licença

Este projeto está em desenvolvimento e é mantido pela EduData IA.