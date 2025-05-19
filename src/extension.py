

def extension_processing(conf) :
    
        if conf.verbose :  
            print("\t - " + "extension processing started : ", conf.extname)
        import importlib
        try:
            module = importlib.import_module(conf.extname, package = None)
        except :
            if conf.verbose : print("\t - " + "import extension failed:", conf.extname)
            return

        try:
            ext_result = module.grottext(conf,result_string,jsonmsg)
            if conf.verbose :
                print("\t - " + "extension processing ended : ", ext_result)
        except Exception as e:
            print("\t - " + "extension processing error:", repr(e))
            if conf.verbose:
                import traceback
                print("\t - " + traceback.format_exc())