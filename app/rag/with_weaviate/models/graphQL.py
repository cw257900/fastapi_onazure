# queries.py

# Define the GraphQL queries as static variables (Python strings)


gql_getAllObjects = """
X-Openai-Api-Key


"""

gql_hybridsearch_withLimits =  """
{
    Get {
        %s(
            hybrid: {
                query: "%s",
                alpha: 0.75
            }
            limit: %d ), 
        {
            source
            page_content
            page_number
            _additional {
                distance
                score
                explainScore
            }
        }
    }
}
"""

gql_hybridSearchByText = """
{
    Get {
        %s(
            hybrid: {
                query: "{text}",
                alpha: 0.75
            }
            ) {
            pdf_number
            pdf_content
            source
             _additional {
                score
                distance
                explainScore
            }
        }
    }

}
"""

gql_getSingleObjectById = """
{
    Get {
        %s(where: {
            path: ["_additional", "id"],
            operator: Equal,
            valueString: "{uuid}"
        }) {
            pdf_number
            pdf_content
            _additional {
                score
                distance
                explainScore
            }
        }
    }
}
"""

gql_queryObjectsByKeyword = """
{
    Get {
        %s(where: {
            path: ["pdf_content"],
            operator: Like,
            valueString: "{keyword}"
        }) {
            pdf_name
            pdf_content
            source
            _additional {
                score
                distance
                explainScore
            }
        }
    }
}
"""

gql_getAllObjects = """
{
    Get {
        %s {
            pdf_name
            pdf_content
            pdf_chunk_id
            _additional {
                id
            }
        }
    }
}
"""
