module example;

    int lo, med, hi;
    bit result;
    int selected;

    initial begin
        lo = 20;
        med = 164;
        hi = 224;

        result = (lo < med) && (med < hi);

        if (result)
            selected = med;
        else
            selected = hi;
    end

endmodule

// Gabarito: result = 1; selected = 164
