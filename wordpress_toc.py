#!/home/bluegala/virtualenv/cgi/2.7/bin/python

#-------------------------------------------------------------------------------
# Name:         Wordpress TOC
# Purpose:      Use Python to query MySQL Wordpress database in order to create an ordered TOC
#               of all Wordpress.org site contents, ordered by number of articles per category and sub-category.
#
# Author:       Chris Nielsen
#
# Created:      11/07/2017
# Copyright:    (c) Chris Nielsen 2018
#-------------------------------------------------------------------------------

import MySQLdb

site_url = 'http://bluegalaxy.info/codewalk'
ent_symbol = r'<span class="ent-symbol">&#9724;</span>'
post_category = {}
post_title_dates = {}
post_links = {}
category_parent = {}
parent_children = {}

main_query = """
SELECT p.post_title as 'Post Title',
	   t.name as 'Category',
	   p.post_date as "Post Date",
	   p.post_name as "Post Name",
       tx.parent as "parent_id",
       t.term_id as "term_id"
FROM wp_posts p,
	 wp_terms t,
	 wp_term_relationships tr,
	 wp_term_taxonomy tx
WHERE p.post_type = 'post'
AND p.post_status = 'publish'
AND tx.taxonomy = 'category'
AND p.ID = tr.object_id
AND tr.term_taxonomy_id = t.term_id
AND tx.term_id = t.term_id;
"""

def print_output(output):
    print "Content-type: text/html\n\n"
    print "<html><head>"
    css = """
    <link rel='stylesheet' id='dashicons-css'  href='http://bluegalaxy.info/codewalk/wp-includes/css/dashicons.min.css?ver=4.8.2' type='text/css' media='all' />
    <link rel='stylesheet' id='admin-bar-css'  href='http://bluegalaxy.info/codewalk/wp-includes/css/admin-bar.min.css?ver=4.8.2' type='text/css' media='all' />
    <link rel='stylesheet' id='cntctfrm_form_style-css'  href='http://bluegalaxy.info/codewalk/wp-content/plugins/contact-form-plugin/css/form_style.css?ver=4.0.7' type='text/css' media='all' />
    <link rel='stylesheet' id='cool-tag-cloud-css'  href='http://bluegalaxy.info/codewalk/wp-content/plugins/cool-tag-cloud/inc/cool-tag-cloud.css?ver=4.8.2' type='text/css' media='all' />
    <link rel='stylesheet' id='googlefonts-css'  href='http://fonts.googleapis.com/css?family=Roboto:400|Off:400&subset=latin' type='text/css' media='all' />
    <link rel='stylesheet' id='hemingway-rewritten-fonts-css'  href='https://fonts.googleapis.com/css?family=Raleway%3A400%2C300%2C700%7CLato%3A400%2C700%2C400italic%2C700italic&#038;subset=latin%2Clatin-ext' type='text/css' media='all' />
    <link rel='stylesheet' id='hemingway-rewritten-style-css'  href='http://bluegalaxy.info/codewalk/wp-content/themes/hemingway-rewritten-wpcom/style.css?ver=4.8.2' type='text/css' media='all' />
    <link rel='stylesheet' id='genericons-css'  href='http://bluegalaxy.info/codewalk/wp-content/themes/hemingway-rewritten-wpcom/genericons/genericons.css?ver=4.8.2' type='text/css' media='all' />
    <link rel='stylesheet' id='enlighter-local-css'  href='http://bluegalaxy.info/codewalk/wp-content/plugins/enlighter/resources/EnlighterJS.min.css?ver=3.5' type='text/css' media='all' />
    <link rel='stylesheet' id='enlighter-external-chris-css'  href='http://bluegalaxy.info/codewalk/wp-content/themes/hemingway-rewritten-wpcom/enlighter/chris.css?ver=aa4c87dc64' type='text/css' media='all' />
    <script type='text/javascript' src='http://bluegalaxy.info/codewalk/wp-includes/js/jquery/jquery.js?ver=1.12.4'></script>
    <script type='text/javascript' src='http://bluegalaxy.info/codewalk/wp-includes/js/jquery/jquery-migrate.min.js?ver=1.4.1'></script>

    <style type='text/css' media='screen'>
		body{ font-family:"Roboto", arial, sans-serif;}
		h1{ font-family:"Roboto", arial, sans-serif;}
		h2{ font-family:"Roboto", arial, sans-serif;}
		h3{ font-family:"Roboto", arial, sans-serif;}
		h4{ font-family:"Roboto", arial, sans-serif;}
		h5{ font-family:"Roboto", arial, sans-serif;}
		h6{ font-family:"Roboto", arial, sans-serif;}

	  #category {
	    margin-left:10px;
	    font-weight: bold;
	  }
	  #sub_category { margin-left:50px; font-weight: bold; }
	  #cat_links a, #sub_cat_links a {
	    margin-left: 50px;
	    color: #141f1f;
	    line-height: 28px;
	    font-family:"Roboto", arial, sans-serif;
	  }
	  #cat_links a:hover, #sub_cat_links a:hover {
	    color: #fff;
	    background-color: #66b3ff;
	  }
	  # #cat_links a:visited, #sub_cat_links a:visited {
	  #   color: #b800e6;
	  #   background-color: #efefef;
	  # }
	  #sub_cat_links { margin-left:100px; }
	  .ent-symbol {
	    font-size: 22px;
	  }
	  @media (max-width: 768px) {
	    #category,
	    #sub_category,
	    #sub_cat_links,
	    #cat_links a,
	    #sub_cat_links a { margin-left: 0px; }
	  }
    </style>
    """
    print css
    print "</head><body>"

    # Process the query results
    categories = set()
    parent_cats = set()
    cat_counts = {}
    global post_category
    global post_title_dates
    global post_links
    global category_parent
    global parent_children
    global output_tuple
    global ent_symbol
    output_tuple = output


    for tup in output:

        post_title = tup[0]
        category = tup[1]
        post_timestamp = tup[2]
        post_date = str(post_timestamp).split()[0]
        post_date = post_date.replace('-', '/')
        title_slug = tup[3]
        parent = tup[4]
        term_id = tup[5]

        # If the post category has a parent
        if parent != 0:
            parent_category = get_cat_name_from_term_id(parent)
            parent_cats.add(parent_category)

            if parent_category not in parent_children.keys():
                parent_children[parent_category] = [category]
            else:
                if category not in parent_children[parent_category]:
                    parent_children[parent_category].append(category)

            # category_parent = { child_category : parent_category }
            if category not in category_parent.keys():
                category_parent[category] = parent_category

        # post_category = { category : post_title }
        if category not in post_category.keys():
            post_category[category] = [post_title] # list of post titles are associated to a category
        else:
            post_category[category].append(post_title)

        # Add post_title as key and post_timestamp as value
        # post_title_dates = { post_title : post_timestamp }
        post_title_dates[post_title] = post_timestamp

        # print output to the web browser (for testing)
        static_link = site_url + '/' + post_date + '/' + title_slug + '/'

        categories.add(category)

        # Add post_title as key and static_link as value
        post_links[post_title] = static_link

        if category not in cat_counts.keys():
            cat_counts[category] = 1
        else:
            cat_counts[category] += 1

##    print "<BR><BR>category_parent", category_parent
##    print "<BR>parent_category", parent_category
##    print "<BR>parent_cats", parent_cats
##    print "<BR>parent_children", parent_children

    # Fix cat_counts so that it contains counts for parents, but not children
    child_cat_counts = {}
    for key in cat_counts.keys():
        if key in category_parent.keys():
            child_cat_counts[key] = cat_counts[key]
            del cat_counts[key]

    # Lets make the TOC Categories order dynamic, based on the number of posts in a category.
    # Sort the categories into order by most posts first
    category_order = []
    for w in sorted(cat_counts.keys(), key=lambda x:cat_counts[x], reverse=True):
      category_order.append(w)

    # Fix category_order so that child categories are injected after their parents
    child_order = []
    for n in sorted(child_cat_counts.keys(), key=lambda x:child_cat_counts[x], reverse=True):
      child_order.append(n)

##    print "<BR><BR>Category order:", category_order
##    print "<BR>cat_counts:", cat_counts
##    print "<BR>child_cat_counts:", child_cat_counts
##    print "<BR>child_order:", child_order

    for category in category_order:
        if category in parent_cats:     # This is a parent
            print "<div id='category'><h4>", category, "</h4></div>"

            child_cat_order = []
            children = parent_children[category]
            for e in child_order:
                if e in children:
                    child_cat_order.append(e)

            # Get all of the sub_cat posts into a list
            sub_cat_post_list_all = []
            for sub_cat in child_cat_order:
                sub_cat_post_list = category_sorted_by_date(sub_cat)
                sub_cat_post_list_all = sub_cat_post_list_all + sub_cat_post_list

            # Case where parent has posts that are directly under the parent
            post_list = category_sorted_by_date(category)
            for post in post_list:
                if post not in sub_cat_post_list_all:   # meaning it is not under a sub_cat
                    link = post_links[post]
                    link_tag = "<a href='%s' target='_parent'>" % (link)
                    print "<div id='cat_links'>", link_tag, ent_symbol, post, "</a></div>"

            for sub_cat in child_cat_order:
                print "<div id='sub_category'><h4>", sub_cat, "</h4></div>"
                sub_cat_post_list = category_sorted_by_date(sub_cat)
                for post in sub_cat_post_list:
                    link = post_links[post]
                    link_tag = "<a href='%s' target='_parent'>" % (link)
                    print "<div id='sub_cat_links'>", link_tag, ent_symbol, post, "</a></div>"
        else:
            print "<div id='category'><h4>", category, "</h4></div>"
            post_list = category_sorted_by_date(category)
            if category not in parent_cats:
                for post in post_list:
                    link = post_links[post]
                    link_tag = "<a href='%s' target='_parent'>" % (link)
                    print "<div id='cat_links'>", link_tag, ent_symbol, post, "</a></div>"

    print "</body></html>"


def get_cat_name_from_term_id(tid):
    global output_tuple
    for tup in output_tuple:
        category = tup[1]
        term_id = tup[5]
        if tid == term_id:
            return category


def category_sorted_by_date(category):
    global post_category
    global post_title_dates

    # Get all of the posts for the given category
    category_posts = post_category[category]

    # Create a small dictionary of post title/dates
    # Add post_title as key and post_date as value
    cat_title_dates = {}
    for post in category_posts:
        cat_title_dates[post] = post_title_dates[post]

    category_order = []
    for w in sorted(cat_title_dates.keys(), key=lambda x:cat_title_dates[x], reverse=True):
      category_order.append(w)

    # List of post names, most recent first, oldest last
    return category_order

def retrieveConnectionDetails():
    # Retrieve the stored database connection details
    connectionDetails = 'connection.txt'
    with open(connectionDetails, 'r') as f:
        lines = f.readlines()

    credentialsDict = {}
    for line in lines:
        kvPair = line.rstrip().split(':')
        credentialsDict[kvPair[0]] = kvPair[1]
    return credentialsDict

def connect(sql):
    # Connect to the database
    creds = retrieveConnectionDetails()
    # Hostname, Username, password, MySQL database name
    connection = MySQLdb.connect(creds['hostname'], creds['username'], creds['password'], creds['database_name'])
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
    except:
        print("Error: unable to fecth data")
    connection.close()
    return result



if __name__ == '__main__':

    result = connect(main_query)
    print_output(result)
