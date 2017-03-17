import utils


def get_signatures_from_bug(bug_id):
    url = 'https://bugzilla.mozilla.org/rest/bug'
    response = utils.get_with_retries(url, params={'id': bug_id})
    response.raise_for_status()
    return response.json()['bugs'][0]['cf_crash_signature']


if __name__ == "__main__":
    get_signatures_from_bug('1308863')
