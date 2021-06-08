def intro(user, timerange, url):
    return f"""Dear reader.
    This paper is a summary of the github activity of {user}\\footnote{{{url}}} between {timerange[0]} and {timerange[1]}.
    This may include repo and gist creation, updates and code changes.
    Please be aware that the paper is generated automatically by a python script so it is not hundred percent relatable.
    I hope the paper will give you a nice overview over the projects and code generation by {user}.
    Feel free to write suggestions on improvements!
    Have a nice read."""

def projects(user, timerange, count):
    return f"""{user} created or contributed to {count} projects between {timerange[0]} and {timerange[1]}."""