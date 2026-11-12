"""Gold answers authored after reading the seven PDFs; excerpts checked locally."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
docs = json.loads((root / 'data/extracted/documents.json').read_text(encoding='utf8'))
rows = []


def add(category, question, answer, passages, key_points):
    evidence = []
    for doc_index, page, needle in passages:
        doc = docs[doc_index - 1]
        block = next(b for b in doc['pages'][page-1]['blocks'] if needle in b['text'] or needle in b['section'])
        evidence.append({'document': doc['reference'], 'file': doc['file'], 'page': page,
                         'section': block['section'], 'excerpt': block['text']})
    rows.append({'id': f'Q{len(rows)+1:02}', 'category': category, 'question': question,
                 'expected_answer': answer, 'key_points': key_points, 'evidence': evidence,
                 'expected_refusal': category == 'hors_corpus'})


add('simple', "Combien de places de semestre d'études sont ouvertes pour 2027-2028 ?", '16 places, dont 5 en double diplôme.', [(3,2,'Au total, 16')], ['16 places', '5 en double diplôme'])
add('simple', 'Quel délai faut-il respecter pour déposer une convention de stage ?', 'Au moins 15 jours calendaires avant le début du stage, convention signée par les trois parties.', [(2,1,'2.2 Convention')], ['15 jours calendaires', 'trois parties'])
add('simple', "Quelle est la durée minimale du stage d'initiation ?", '4 semaines entre le 1er juillet et le 31 août.', [(2,2,"3. Stage d'initiation")], ['4 semaines', '1er juillet', '31 août'])
add('simple', 'Combien de fondateurs faut-il pour créer un club et quelles pièces déposer ?', "Au moins 10 étudiants fondateurs, un enseignant référent, les statuts et une présentation des objectifs et activités ; dossier au BVE.", [(5,2,'4.2 Créer')], ['10', 'enseignant référent', 'statuts', 'objectifs', 'BVE'])
add('simple', 'Quel est le délai pour justifier une absence ?', "48 heures suivant la fin de l'absence ; justificatif au Service de la Scolarité ou sur le portail.", [(1,2,'Article 6')], ['48 heures', "fin de l'absence", 'Scolarité'])
add('simple', 'En combien de temps obtient-on une attestation de scolarité ?', 'Sous 3 jours ouvrables après demande sur le Portail Scolarité, rubrique Mes documents.', [(6,1,'Q1.')], ['3 jours ouvrables', 'Portail Scolarité'])
add('simple', 'Quel est le plafond de subvention annuelle pour un club ?', '15 000 MAD par club et par an.', [(5,3,'4.3 Financement')], ['15 000 MAD', 'par club et par an'])
add('simple', "Quel est le montant de l'aide forfaitaire au voyage en mobilité ?", "3 000 MAD versés une seule fois pour les étudiants retenus pour un semestre d'études ou un double diplôme.", [(3,3,'Aide forfaitaire au voyage')], ['3 000 MAD', 'une seule fois'])
add('synthese', "Comment m'inscrire au rattrapage de S3 en 2026-2027 et à quelle date limite ?", 'Inscription obligatoire sur le Portail Scolarité dans les 5 jours ouvrables suivant les résultats ; date limite le 12 février 2027.', [(1,3,'Article 14'),(4,1,"Date limite d'inscription au rattrapage")], ['obligatoire', '5 jours ouvrables', '12 février 2027'])
add('synthese', "Je pars en mobilité S5 : comment et quand soutenir mon stage technique ?", 'Stage effectué avant le départ ; soutenance en octobre en visioconférence. Le calendrier indique du 4 au 15 octobre 2026 (ses libellés de jours sont à reprendre avec prudence).', [(2,2,'4. Stage technique'),(3,3,'6.4 Stage technique'),(4,1,'Soutenances des stages techniques')], ['avant le départ', 'visioconférence', 'octobre'])
add('synthese', "Comment demander un aménagement d'épreuves et à quelle échéance en 2026 ?", "Droit conditionné à la décision d'une commission ; rendez-vous au référent accessibilité du BVE, certificat médical récent et dépôt avant le 30 octobre 2026 ; en cours d'année, dans les 15 jours du diagnostic ou de l'apparition.", [(1,2,'Article 10'),(5,2,'3.1 Procédure'),(4,1,"Date limite des demandes d'aménagement")], ['BVE', 'certificat médical', '30 octobre', '15 jours', 'commission'])
add('synthese', 'Comment faire valider mon sujet de PFE et quand déposer la fiche pour 2026-2027 ?', 'Fiche sujet sur le Portail Stages ; validation par le responsable de filière ; date limite le 15 décembre 2026.', [(2,2,'5.2 Choix'),(4,1,'Date limite de dépôt de la fiche sujet')], ['Portail Stages', 'responsable de filière', '15 décembre 2026'])
add('synthese', 'Comment candidater à une mobilité 2027-2028 et quand déposer le dossier ?', 'Être en 2A, moyenne S3 au moins 12/20 (14/20 pour double diplôme), langue B2, aucune sanction ; dossier CV, lettre, relevé S3, certificat de langue, trois vœux avant le 15 mars 2027 ; confirmation après validation 2A sans dette et moyenne annuelle au moins 12/20.', [(3,2,"4. Conditions"),(3,2,'Dépôt du dossier'),(4,2,'Date limite de candidature')], ['2A', '12/20', '14/20', 'B2', '15 mars 2027', 'sans dette'])
add('version', 'Pour un PFE débutant en février 2027, la durée minimale est-elle 16 ou 18 semaines ?', "18 semaines, maximum 24. La note du 5 octobre 2026 remplace explicitement les dispositions correspondantes du guide du 15 juin 2026 (16 semaines) et vise les PFE débutant à partir du 1er février 2027, y compris à l'étranger.", [(2,2,'5.3 Durée'),(7,1,'remplacent les dispositions'),(7,1,'Article 1'),(7,2,'Article 4')], ['18 semaines', '24', '16', '1er février 2027', 'remplace'])
add('version', 'Pour mon PFE 2027, dois-je déposer le rapport 10 ou 14 jours avant la soutenance ?', "14 jours calendaires. La note du 5 octobre 2026 remplace le délai de 10 jours du guide ; elle concerne les PFE débutant à partir du 1er février 2027, y compris à l'étranger.", [(2,3,'5.5 Rapport'),(7,1,'remplacent les dispositions'),(7,1,'Article 2'),(7,2,'Article 4')], ['14 jours', 'calendaires', '10 jours', '1er février 2027', 'remplace'])
refusal = "Je ne trouve pas cette information dans les documents de l'École."
for question in ["Quel est le prix d'un repas au restaurant de l'École ?", "Le stage d'initiation est-il rémunéré ?", "Quel est le mot de passe du Wi-Fi étudiant ?", "Quel est le classement mondial de l'EIH ?", "Quelle météo fera-t-il à l'École demain ?"]:
    add('hors_corpus', question, refusal, [], [])
target = root / 'eval/questions.jsonl'
target.write_text('\n'.join(json.dumps(row, ensure_ascii=False) for row in rows)+'\n', encoding='utf8')
print(len(rows), 'questions avec preuves vérifiées')
