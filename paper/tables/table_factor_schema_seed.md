| Factor | Level | Allowed roles | Parents | Description |
|---|---|---|---|---|
| entity | universal | subject_domain, object_domain, value_domain, background |  | Generic entity or concept. |
| person | universal | subject_domain, object_domain, value_domain, background | entity | Human individual or person-like agent. |
| place | universal | subject_domain, object_domain, value_domain, background | entity | Location, city, country, region, or spatial object. |
| organization | universal | subject_domain, object_domain, value_domain, background | entity | Institution, company, team, university, or formal group. |
| creative_work | domain | subject_domain, object_domain, value_domain, background | entity | Work, character, song, book, artwork, or cultural artifact. |
| event | universal | subject_domain, object_domain, value_domain, background | entity | Event or historically bounded occurrence. |
| time | universal | subject_domain, object_domain, value_domain, background |  | Date, period, epoch, or temporal value. |
| quantity | universal | subject_domain, object_domain, value_domain, background |  | Numeric value, scalar quantity, count, or physical magnitude. |
| measurement | scientific | subject_domain, object_domain, value_domain, background, predicate_meaning |  | Measured property or value-bearing observation. |
| language | domain | subject_domain, object_domain, value_domain, background | entity | Natural language or language attribute. |
| identifier | domain | subject_domain, object_domain, value_domain, background |  | Code, database identifier, location identifier, or registry key. |
| entity_relation | abstract_relation | predicate_meaning, modifier, background |  | Generic relation between graph entities. |
| biographical_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Birth, death, nationality, occupation, and person-level biography facts. |
| location_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Spatial containment, location, country, city, or place association. |
| part_whole_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Membership, containment, part-of, or whole-part structure. |
| membership_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Affiliation, club, team, membership, or participation relation. |
| political_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Leadership, mayor, capital, governance, or office relation. |
| creative_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Creator, author, artist, band, work, or cultural production relation. |
| organizational_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Company, university, headquarters, operation, or institutional relation. |
| astronomical_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Celestial-body and astronomy-specific relation. |
| sports_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Athlete, club, team, ground, or sport competition relation. |
| transport_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Airport, runway, vehicle, infrastructure, or transport relation. |
| language_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Language-used, language-of-work, or language attribute relation. |
| identifier_relation | abstract_relation | predicate_meaning, modifier, background | entity_relation | Identifier-bearing relation such as ICAO or location codes. |
