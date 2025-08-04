import { get } from "jquery";

var g_recommendation_id = null;
var g_recommendation_desc_editor = null;

function edit_in_recommendation_desc() {
    if($('#container_recommendation_desc_content').is(':visible')) {
        $('#container_recommendation_description').show(100);
        $('#container_recommendation_desc_content').hide(100);
        $('#recommendation_edition_btn').hide(100);
        $('#recommendation_preview_button').hide(100);
    } else {
        $('#recommendation_preview_button').show(100);
        $('#recommendation_edition_btn').show(100);
        $('#container_recommendation_desc_content').show(100);
        $('#container_recommendation_description').hide(100);
    }
}

/* Fetch a modal that allows to import recommendations */
function import_recommendation() {
    console.log("import clicked");
    url = 'recommendations/import/modal' + case_param();
    $('#modal_add_recommendation_content').load(url, function (response, status, xhr) {
        //hide_minimized_modal_box();
        if (status !== "success") {
            console.error("Failed to load import recommendations modal:", xhr);
            ajax_notify_error(xhr, url);
            return false;
        }

        console.log("first if passed");

        get_request_api('/manage/recommendations/list')
        .done((data) => {
            if (api_request_failed(data)) {
                console.error("Failed to fetch global recommendations:", data);
                return;
            }

            if (data.data.length === 0) {
                console.log("No global recommendations available.");
                $('#import_global_recommendations').hide();
                $('#no_global_recommendations').show();
            } else {
                $('#modal_import_case_recommendations').show();
                $('#no_global_recommendations').hide();
                console.log("Global recommendations loaded:", data.data);
            }

            $('.list-group').empty();
            $.each(data.data, function(index, recommendation) {
                console.log("Listing global recommendation:", recommendation.title);
                let item = $('<a>')
                    .addClass('list-group-item list-group-item-action')
                    .attr('href', 'javascript:void(0);')
                    .attr('data-recommendation_id', recommendation.id)
                    .attr('title', `Recommendation ID #${recommendation.id} - ${recommendation.title}`)
                    .text(recommendation.description)
                    .on('click', function() {
                        let recommendation_id = $(this).data('recommendation_id');
                        let case_id = get_caseid();
                        post_request_api(`/api/v2/cases/${case_id}/recommendations/${recommendation_id}/import`, null, true)
                        .done((data, textStatus) => {
                            if (textStatus === 'success') {
                                notify_success(`Recommendation #${recommendation_id} imported successfully.`);
                                //get_recommendations();
                                $('#modal_import_case_recommendations').modal('show');
                            } else {
                                notify_error(`Error importing recommendation #${recommendation_id}.`);
                            }
                        });
                    });
                $('.list-group').append(item);
            });
        })
        .fail((xhr, status, error) => {
            console.error("Error fetching global recommendations:", error);
            $('.list-group').html('<div class="text-danger">Error loading recommendations.</div>');
        }
        );
    });

    //var global_recs = get_request_api('/manage/recommendations/list'); 
    //console.log(global_recs);

   // $('#modal_import_recommendations').modal({ show: true });
}

/* Fetch a modal that allows to add an event */
function add_recommendation() {
    url = 'recommendations/add/modal' + case_param();
    $('#modal_add_recommendation_content').load(url, function (response, status, xhr) {
        hide_minimized_modal_box();
        if (status !== "success") {
             ajax_notify_error(xhr, url);
             return false;
        }
        
        g_recommendation_desc_editor = get_new_ace_editor('recommendation_description', 'recommendation_desc_content', 'target_recommendation_desc',
                            function() {
                                $('#last_saved').addClass('btn-danger').removeClass('btn-success');
                                $('#last_saved > i').attr('class', "fa-solid fa-file-circle-exclamation");
                            }, null);
        g_recommendation_desc_editor.setOption("minLines", "10");
        edit_in_recommendation_desc();

        headers = get_editor_headers('g_recommendation_desc_editor', null, 'recommendation_edition_btn');
        $('#recommendation_edition_btn').append(headers);

        $('#submit_new_recommendation').on("click", function () {

            clear_api_error();
            if(!$('form#form_new_recommendation').valid()) {
                return false;
            }

            var data_sent = $('#form_new_recommendation').serializeObject();
            data_sent['recommendation_tags'] = $('#recommendation_tags').val();
            data_sent['recommendation_description'] = g_recommendation_desc_editor.getValue();
            ret = get_custom_attributes_fields();
            has_error = ret[0].length > 0;
            attributes = ret[1];

            if (has_error){return false;}

            data_sent['custom_attributes'] = attributes;
            case_id =  get_caseid()
            post_request_api(`/api/v2/cases/${case_id}/recommendations`, JSON.stringify(data_sent), true)
            .done((data, textStatus) => {
                if(textStatus === 'success') {
                    get_recommendations();
                    $('#modal_add_recommendation').modal('hide');
                }
            });

            return false;
        })
        $('#modal_add_recommendation').modal({ show: true });
        $('#recommendation_title').focus();

    });

}

function save_recommendation() {
    $('#submit_new_recommendation').click();
}

function update_recommendation(recommendation_id) {
    update_recommendation_ext(recommendation_id, true);
}

function update_recommendation_ext(recommendation_id, do_close) {

    clear_api_error();
    if(!$('form#form_new_recommendation').valid()) {
        return false;
    }

    if (recommendation_id === undefined || recommendation_id === null) {
        recommendation_id = g_recommendation_id;
    }

    var data_sent = $('#form_new_recommendation').serializeObject();
    data_sent['recommendation_tags'] = $('#recommendation_tags').val();

    ret = get_custom_attributes_fields();
    has_error = ret[0].length > 0;
    attributes = ret[1];

    if (has_error){return false;}

    data_sent['custom_attributes'] = attributes;
    data_sent['recommendation_description'] = g_recommendation_desc_editor.getValue();

    $('#update_recommendation_btn').text('Updating..');

    post_request_api(`/case/recommendations/update/${recommendation_id}`, JSON.stringify(data_sent), true)
    .done((data) => {
        if(notify_auto_api(data)) {
            get_recommendations();
            $('#submit_new_recommendation').text("Saved").addClass('btn-outline-success').removeClass('btn-outline-danger').removeClass('btn-outline-warning');
            $('#last_saved').removeClass('btn-danger').addClass('btn-success');
            $('#last_saved > i').attr('class', "fa-solid fa-file-circle-check");

            if (do_close !== undefined && do_close === true) {
                $('#modal_add_recommendation').modal('hide');
            }
        }
    })
    .always(() => {
        $('#update_recommendation_btn').text('Update');
    });
}

/* Delete an event from the timeline thank to its id */ 
function delete_recommendation(id) {
    do_deletion_prompt("You are about to delete recommendation #" + id)
    .then((doDelete) => {
        if (doDelete) {
            let cid = get_caseid();
            delete_request_api(`/api/v2/cases/${cid}/recommendations/${id}`)
            .done((data, textStatus) => {
                 if (textStatus === 'nocontent') {
                    get_recommendations();
                    $('#modal_add_recommendation').modal('hide');
                    notify_success('Recommendation deleted');
                } else {
                     notify_error('Error deleting recommendation')
                 }
            });
        }
    });
}

/* Edit and event from the timeline thanks to its ID */
function edit_recommendation(id) {
  url = `/case/recommendations/${id}/modal${case_param()}`;
  $('#modal_add_recommendation_content').load(url, function (response, status, xhr) {
        hide_minimized_modal_box();
        if (status !== "success") {
             ajax_notify_error(xhr, url);
             return false;
        }

        g_recommendation_id = id;

        g_recommendation_desc_editor = get_new_ace_editor('recommendation_description', 'recommendation_desc_content', 'target_recommendation_desc',
                            function() {
                                $('#last_saved').addClass('btn-danger').removeClass('btn-success');
                                $('#last_saved > i').attr('class', "fa-solid fa-file-circle-exclamation");
                            }, null);

        g_recommendation_desc_editor.setOption("minLines", "6");
        preview_recommendation_description(true);

        headers = get_editor_headers('g_recommendation_desc_editor', null, 'recommendation_edition_btn');
        $('#recommendation_edition_btn').append(headers);

        load_menu_mod_options_modal(id, 'recommendation', $("#recommendation_modal_quick_actions"));
        $('#modal_add_recommendation').modal({show:true});
        edit_in_recommendation_desc();
  });
}

function preview_recommendation_description(no_btn_update) {
    if(!$('#container_recommendation_description').is(':visible')) {
        recommendation_desc = g_recommendation_desc_editor.getValue();
        converter = get_showdown_convert();
        html = converter.makeHtml(do_md_filter_xss(recommendation_desc));
        recommendation_desc_html = do_md_filter_xss(html);
        $('#target_recommendation_desc').html(recommendation_desc_html);
        $('#container_recommendation_description').show();
        if (!no_btn_update) {
            $('#recommendation_preview_button').html('<i class="fa-solid fa-eye-slash"></i>');
        }
        $('#container_recommendation_desc_content').hide();
    }
    else {
        $('#container_recommendation_description').hide();
         if (!no_btn_update) {
            $('#recommendation_preview_button').html('<i class="fa-solid fa-eye"></i>');
        }

        $('#recommendation_preview_button').html('<i class="fa-solid fa-eye"></i>');
        $('#container_recommendation_desc_content').show();
    }
}

/* Fetch and draw the recommendations */
function get_recommendations() {
    show_loader();

    get_request_data_api('/case/recommendations/state').done((response, textStatus) => {
        if (textStatus !== 'success') {
            return;
        }
        set_last_state(response.data);
    });

    get_request_data_api(`/api/v2/cases/${get_caseid()}/recommendations`, { 'per_page': Number.MAX_SAFE_INTEGER })
    .done((data, textStatus) => {
        console.log(data);
        if (textStatus !== 'success') {
            Table.clear().draw()
            return;
        }

        if (data == null) {
            Table.clear().draw();
            swal("Oh no !", data.message, "error")
            return;
        }

        Table.clear();
        Table.rows.add(data.data);

        $('#recommendation_table_wrapper').on('click', function(e){
            if($('.popover').length>1)
                $('.popover').popover('hide');
                $(e.target).popover('toggle');
            });

        $('#recommendations_table_wrapper').show();
        Table.columns.adjust().draw();
        load_menu_mod_options('recommendation', Table, delete_recommendation);
        hide_loader();
        Table.responsive.recalc();

        $(document)
            .off('click', '.recommendation_details_link')
            .on('click', '.recommendation_details_link', function(event) {
            event.preventDefault();
            let recommendation_id = $(this).data('recommendation_id');

            edit_recommendation(recommendation_id);
        });
    });
}


// function refresh_users(on_finish, cur_assignees_id_list) {

//     get_request_api('/case/users/list')
//     .done((data) => {
//         if (api_request_failed(data)) {
//             return;
//         }

//         current_users_list = data.data;
//         if (on_finish !== undefined) {
//             on_finish(current_users_list, cur_assignees_id_list);
//         }
//     });

// }

/* Page is ready, fetch the assets of the case */
$(document).ready(function(){

    /* add filtering fields for each table of the page (must be done before datatable initialization) */
    $.each($.find("table"), function(index, element){
        addFilterFields($(element).attr("id"));
    });

    Table = $("#recommendations_table").DataTable({
        dom: '<"container-fluid"<"row"<"col"l><"col"f>>>rt<"container-fluid"<"row"<"col"i><"col"p>>>',
        aaData: [],
        fixedHeader: true,
        aoColumns: [
          {
            "data": "recommendation_title",
            "render": function (data, type, row, meta) {
              if (type === 'display' && data != null) {

                let datak = '';
                let anchor = $('<a>')
                    .attr('href', 'javascript:void(0);')
                    .attr('data-recommendation_id', row['id'])
                    .attr('title', `Recommendation ID #${row['id']} - ${data}`)
                    .addClass('recommendation_details_link')

                if (isWhiteSpace(data)) {
                    datak = '#' + row['id'];
                    anchor.text(datak);
                } else {
                    datak= ellipsis_field(data, 64);
                    anchor.html(datak);
                }

                return anchor.prop('outerHTML');
              }
              return data;
            }
          },
          { "data": "recommendation_description",
           "render": function (data, type, row, meta) {
              if (type === 'display') {
                  return ret_obj_dt_description(data);
              }
              return data;
            }
          }
        ],
        rowCallback: function (nRow, data) {
            nRow = '<span class="badge ml-2 badge-'+ sanitizeHTML(data['status_bscolor']) +'">' + sanitizeHTML(data['status_name']) + '</span>';
        },
        filter: true,
        info: true,
        ordering: true,
        processing: true,
        retrieve: true,
        pageLength: 50,
        order: [[ 0, "asc" ]],
        buttons: [
        ],
        responsive: {
            details: {
                display: $.fn.dataTable.Responsive.display.childRow,
                renderer: $.fn.dataTable.Responsive.renderer.tableAll()
            }
        },
        orderCellsTop: true,
        initComplete: function () {
            tableFiltering(this.api(), 'recommendations_table');
        },
        select: true
    });
    $("#recommendations_table").css("font-size", 12);

    Table.on( 'responsive-resize', function ( e, datatable, columns ) {
            hide_table_search_input( columns );
    });

    // var buttons = new $.fn.dataTable.Buttons(Table, {
    //      buttons: [
    //         { "extend": 'csvHtml5', "text":'<i class="fas fa-cloud-download-alt"></i>',"className": 'btn btn-link text-white'
    //         , "titleAttr": 'Download as CSV', "exportOptions": { "columns": ':visible', 'orthogonal':  'export' } } ,
    //         { "extend": 'copyHtml5', "text":'<i class="fas fa-copy"></i>',"className": 'btn btn-link text-white'
    //         , "titleAttr": 'Copy', "exportOptions": { "columns": ':visible', 'orthogonal':  'export' } },
    //         { "extend": 'colvis', "text":'<i class="fas fa-eye-slash"></i>',"className": 'btn btn-link text-white'
    //         , "titleAttr": 'Toggle columns' }
    //     ]
    // }).container().appendTo($('#tables_button'));

    get_recommendations();

    setInterval(function() { check_update('/case/recommendations/state'); }, 3000);

    shared_id = getSharedLink();
    if (shared_id) {
        edit_recommendation(shared_id);
    }
});
