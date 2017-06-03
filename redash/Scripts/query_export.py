import click
import requests
import os.path
import os
from os import listdir
from github import Github
from github import InputGitTreeElement
template = u"""/*
Name: {name}
Data source: {data_source}
Created By: {created_by}
Last Update At: {last_updated_at}
*/
{query}
"""


def get_queries(url, api_key):
    queries = []
    headers = {'Authorization': 'Key {}'.format(api_key)}
    path = "{}/api/queries".format(url)

    response = requests.get(path, headers=headers).json()
    queries.extend(response)

    return queries


def save_queries(queries):
    directory = './queries_versioned/'
    if not os.path.exists(directory):
        os.makedirs(directory)

    for query in queries:
        str = query['name']
        for ch in [':', '"',">"]:
            if ch in str:
                str = str.replace(ch, "_")

        filename = '{}_{}.sql'.format(query['id'], str)
        with open(os.path.join(directory,filename), 'w') as f:
            content = template.format(name=query['name'],
                       data_source=query['data_source_id'],
                       created_by=query['user']['name'],
                       last_updated_at=query['updated_at'],
                       query=query['query'])
            f.write(content.encode('utf-8'))
    return directory


def commit_tree(repo,commit_message,new_tree):
	
    master_ref= repo.get_git_ref('heads/master')
    
    latest_commit= repo.get_git_commit(master_ref.object.sha)
	#Create new commit with the An existing tree object
    new_commit = repo.create_git_commit(
            message=commit_message,
            parents=[latest_commit],
            tree=new_tree)
    
    master_ref.edit(sha=new_commit.sha)
	
def get_files_to_upload(directory,repo,branch):
    """
    """
    
    # Prepare files to upload to GitHub
    element_list = []
    for entry in listdir(directory):        
        entry = os.path.join(directory, entry)
        with open(entry,'rb') as input_file:            
            data = input_file.read()
        element = InputGitTreeElement(entry, '100644', 'blob', data)
        element_list.append(element)
        
    
    new_tree = repo.create_git_tree(element_list)
    print new_tree.sha
    
    return new_tree
    
                   
    
def get_instance_repo(user, passw,repository,branch):
	
    """
    Create a Github instance:
    """
    g = Github(user, passw)
    
    for repo in g.get_user().get_repos():
	   if repo.name == repository:
			return repo
		


@click.command()
@click.option('--redash-url')
@click.option('--api-key', help="API Key")
@click.option('--user', help="GitHub user name.")
@click.option('--passw', help="GitHub password.")
@click.option('--message', help="Commit message." , default="Empy message")
@click.option('--branch', help="GitHub branch.", default="master")
@click.option('--repo', help="GitHub repository.")

# EXAMPLE OF COMMAND TO RUN :python query_export.py --redash-url "http://172.16.6.10:9001" --api-key "ynPdQYzT4Yifq9btTWvPaeByZ3PWFI9IzlJ0UPzI" --user jmvasquez --passw Devspark1@1 --repo "mansion-global-analytics-queries" --branch "master" --message "Commit from production"

def main(redash_url, api_key, user, passw, message, branch, repo):
    
    queries = get_queries(redash_url, api_key)
    save_queries(queries)
    folder = 'queries_versioned/'
    
    #Create git instance
    repository= get_instance_repo(user,passw,repo,branch)

    #Create a new commit object with the files to be uploaded   
    new_tree= get_files_to_upload(folder,repository,branch)
    
    #Commit the new tree
    commit_tree(repository,message,new_tree)


if __name__ == '__main__':
    main()
