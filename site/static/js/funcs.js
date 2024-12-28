function next_page(href) {
    window.location.href=href;
}

function reload_page() {
    next_page(window.location.href);
}

function next_page_no_reload(href) {
    history.pushState({}, "", href);
}

function ajax_call(path, get, data) {
    let is_post_method=(data!==undefined && data!==null);
    data=(is_post_method && data instanceof HTMLFormElement) ? (new FormData(data)):data;
    return new Promise((resolve, reject)=>{
        let ajax_req=new XMLHttpRequest();
        ajax_req.open(is_post_method ? "POST":"GET", `${path}/${get}`);
        ajax_req.onreadystatechange=function() {
            if(this.readyState==XMLHttpRequest.DONE)
                if(this.status==200)
                    resolve(ajax_req.responseText);
                else
                    reject({'err_code':ajax_req.status, 'err_mess':ajax_req.responseText});
        };
        if(is_post_method)
            ajax_req.send(data);
        else
            ajax_req.send();
    });
}

function ajax_json_call(path, get, data) {
    return new Promise((resolve, reject)=>{
        ajax_call(path, get, data).then(data=>{
            let json=data;
            try {
                data=JSON.parse(json);
                resolve(data);
            } catch(err) {
                reject({'err_mess': err, 'err_data': json});
            }
        }, err=>{
            reject(err);
        });
    });
}
