import utils


def get_signatures_from_bug(bug_id):
    url = 'https://bugzilla.mozilla.org/rest/bug'
    response = utils.get_with_retries(url, params={'id': bug_id})
    response.raise_for_status()
    signature = []
    for sig in response.json()['bugs'][0]['cf_crash_signature'].split('\r\n'):
        pos = sig.find('[@')
        if pos != -1:
            sig = sig[pos + 2:]
        pos2 = sig.rfind(']')
        if pos2 != -1:
            sig = sig[:pos2]
        signature.append(sig.strip())
    return signature


if __name__ == "__main__":
    print(get_signatures_from_bug('1333486'))
