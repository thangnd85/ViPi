/**
 *
 * Author  : Pawan Singh Pal
 * Email   : pawansingh126@gmail.com
 * Date    : Oct 2018
 *
 */

/**
 * Calls /save URL to save edit progress.
 * @param  {String} data Stringified JSON data.
 */
function save(data) {
    $.ajax({
        type: 'POST',
        url: '/save',
        data: data,
        success: function(res) {
            setTimeout(function() { alert(res); }, 3);
        },
        contentType: 'application/json;charset=UTF-8'
    });
}

/**
 * Calls /saveExit URL to save edit progress and shut down web server.
 * @param  {String} data Stringified JSON data.
 */
function saveAndExit(data) {
    $.ajax({
        type: 'POST',
        url: '/saveExit',
        data: data,
        success: function(res) {
            setTimeout(function() { alert(res); }, 3);
        },
        contentType: 'application/json;charset=UTF-8'
    });
}

/**
 * Collects and validates data from textarea.
 * @returns  {String}  Stringified JSON data.
 */
function getSimpleData() {
    var data = $("#yaml_data").val();
    try {
        var index = data.indexOf(changeStr)
        if (index != -1) {
            var lineNum = data.substring(0, index).split('\n').length;
            alert('Please change value on line '+ lineNum + '!')
            return null
        }
        data = jsyaml.load(data)
    }
    catch(err) {
        alert(err)
        return null
    }
    return JSON.stringify({yaml_data : data})
}

/**
 * Collects and validates data from tree structure.
 * @returns  {String}  Stringified JSON data.
 */
function getTreeData(treeRoot, data={}) {
    $(treeRoot.children).each(function(index, val) {
        switch(val.getAttribute('val')) {
            case 'string':
                data[val.getAttribute('key')] = val.lastChild.value
                break;
            case 'map':
                data[val.getAttribute('key')] = getTreeData(
                    val.lastChild)
                break;
            case 'iter':
                console.log(val.children)
                data[val.getAttribute('key')] = Array()
                break;
        }
    });
    return data
}

/**
 * Function to save edit progress.
 */
function saveSimple() {
    var data = getSimpleData()
    if (data) {
        save(data)
    }
}

/**
 * Function to save edit progress and shut down web server.
 */
function saveExitSimple() {
    var data = getSimpleData()
    if (data) {
        saveAndExit(data)
    }
}

/**
 * Function to save edit progress from tree structure.
 */
function saveTree() {
    save(getTreeData(document.getElementById('tree'), ))
}

/**
 * Function to save edit progress from tree structure and shut down web server.
 */
function saveExitTree() {
    saveAndExit(getTreeData(document.getElementById('tree')))
}
