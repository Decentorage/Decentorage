from controllers import user_signup, user_signin, get_active_contracts, get_state, create_file, get_price, get_file_info, pay_contract, get_decentorage_wallet_address, start_download, get_contract, shard_done_uploading, file_done_uploading
import app
user_url_prefix = '/user'


def add_user_urls():
    # Get Methods
    app.app.add_url_rule(user_url_prefix + "/getFiles", view_func=get_active_contracts, methods=["GET"])
    app.app.add_url_rule(user_url_prefix + "/getState", view_func=get_state, methods=["GET"])
    app.app.add_url_rule(user_url_prefix + "/getPrice", view_func=get_price, methods=["GET"])
    app.app.add_url_rule(user_url_prefix + "/getFileInfo", view_func=get_file_info, methods=["GET"])
    app.app.add_url_rule(user_url_prefix + "/payContract", view_func=pay_contract, methods=["GET"])
    app.app.add_url_rule(user_url_prefix + "/getDecentorageWalletAddress", view_func=get_decentorage_wallet_address,
                         methods=["GET"])
    app.app.add_url_rule(user_url_prefix + "/getContract", view_func=get_contract, methods=["GET"])


    # Post Methods
    app.app.add_url_rule(user_url_prefix + "/signup", view_func=user_signup, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/signin", view_func=user_signin, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/createFile", view_func=create_file, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/startDownload", view_func=start_download, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/shardDoneUploading", view_func=shard_done_uploading, methods=["POST"])
    app.app.add_url_rule(user_url_prefix + "/filedDoneUploading", view_func=file_done_uploading, methods=["POST"])
