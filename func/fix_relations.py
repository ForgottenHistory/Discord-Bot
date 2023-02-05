def fix_relations(preprompt, people_memory):
    
    # Add relationships
    prepromt_fixed = preprompt
    relations = "Relations("
    for person in people_memory:
        value = people_memory[person]
        if value >= 5.5 and value < 9.5:
            relations += f"\"You like {person}\"+"
        elif value >= 9.5:
            relations += f"\"You love {person}\"+"
        elif value > 2.0 and value <= 4.5:
            relations += f"\"You dislike {person}\"+"
        elif value <= 2.0:
            relations += f"\"You hate {person}\"+"

    relations = relations[:-1] + ")"
    
    # Find the index of the closing curly bracket
    index = prepromt_fixed.find("}")

    # Insert the relations before the closing bracket
    prepromt_fixed = prepromt_fixed[:index] + f"{relations}" + prepromt_fixed[index:]

    return prepromt_fixed
